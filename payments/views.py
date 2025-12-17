from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import stripe
import json

from .models import SPVStripeAccount, Payment, PaymentWebhookEvent
from .serializers import (
    SPVStripeAccountSerializer,
    StripeConnectOnboardingSerializer,
    CreatePaymentSerializer,
    PaymentSerializer,
    PaymentListSerializer,
    ConfirmPaymentSerializer,
    PaymentStatisticsSerializer,
)
from spv.models import SPV
from investors.dashboard_models import Investment, Portfolio


# Initialize Stripe
stripe.api_key = getattr(settings, 'STRIPE_SECRET_KEY', None)
STRIPE_WEBHOOK_SECRET = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)
PLATFORM_FEE_PERCENTAGE = getattr(settings, 'PLATFORM_FEE_PERCENTAGE', 2.0)


class SPVStripeAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing SPV Stripe Connect accounts.
    """
    queryset = SPVStripeAccount.objects.all()
    serializer_class = SPVStripeAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user's SPVs"""
        user = self.request.user
        if user.is_staff:
            return SPVStripeAccount.objects.all()
        return SPVStripeAccount.objects.filter(spv__created_by=user)
    
    @action(detail=False, methods=['post'])
    def connect(self, request):
        """
        Initiate Stripe Connect onboarding for an SPV.
        
        POST /api/payments/stripe-accounts/connect/
        {
            "spv_id": 1,
            "return_url": "https://yourapp.com/stripe/success",
            "refresh_url": "https://yourapp.com/stripe/refresh"
        }
        """
        serializer = StripeConnectOnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        spv_id = serializer.validated_data['spv_id']
        return_url = serializer.validated_data.get('return_url', 'http://localhost:3000/stripe/success')
        refresh_url = serializer.validated_data.get('refresh_url', 'http://localhost:3000/stripe/refresh')
        
        try:
            spv = SPV.objects.get(id=spv_id, created_by=request.user)
        except SPV.DoesNotExist:
            return Response(
                {'error': 'SPV not found or you do not have permission'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if account already exists
        if hasattr(spv, 'stripe_account'):
            stripe_account = spv.stripe_account
            
            # If onboarding not complete, generate new link
            if not stripe_account.details_submitted:
                try:
                    account_link = stripe.AccountLink.create(
                        account=stripe_account.stripe_account_id,
                        refresh_url=refresh_url,
                        return_url=return_url,
                        type='account_onboarding',
                    )
                    stripe_account.onboarding_url = account_link.url
                    stripe_account.save()
                    
                    return Response({
                        'message': 'Continue onboarding',
                        'onboarding_url': account_link.url,
                        'stripe_account': SPVStripeAccountSerializer(stripe_account).data
                    })
                except stripe.error.StripeError as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'message': 'Stripe account already connected',
                    'stripe_account': SPVStripeAccountSerializer(stripe_account).data
                })
        
        # Create new Stripe Connect account
        try:
            account = stripe.Account.create(
                type='express',
                country='US',
                email=spv.founder_email,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
                business_type='company',
                metadata={
                    'spv_id': str(spv.id),
                    'spv_name': spv.display_name,
                }
            )
            
            # Create account link for onboarding
            account_link = stripe.AccountLink.create(
                account=account.id,
                refresh_url=refresh_url,
                return_url=return_url,
                type='account_onboarding',
            )
            
            # Save to database
            stripe_account = SPVStripeAccount.objects.create(
                spv=spv,
                stripe_account_id=account.id,
                account_status='onboarding',
                onboarding_url=account_link.url,
            )
            
            return Response({
                'message': 'Stripe Connect account created',
                'onboarding_url': account_link.url,
                'stripe_account': SPVStripeAccountSerializer(stripe_account).data
            }, status=status.HTTP_201_CREATED)
            
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """
        Get Stripe account status for an SPV.
        
        GET /api/payments/stripe-accounts/status/?spv_id=1
        """
        spv_id = request.query_params.get('spv_id')
        if not spv_id:
            return Response({'error': 'spv_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            stripe_account = SPVStripeAccount.objects.get(spv_id=spv_id)
        except SPVStripeAccount.DoesNotExist:
            return Response({'error': 'No Stripe account found for this SPV'}, status=status.HTTP_404_NOT_FOUND)
        
        # Refresh status from Stripe
        try:
            account = stripe.Account.retrieve(stripe_account.stripe_account_id)
            
            stripe_account.charges_enabled = account.charges_enabled
            stripe_account.payouts_enabled = account.payouts_enabled
            stripe_account.details_submitted = account.details_submitted
            
            if account.details_submitted:
                stripe_account.account_status = 'active'
            
            stripe_account.save()
            
        except stripe.error.StripeError as e:
            pass  # Use cached data if Stripe API fails
        
        return Response(SPVStripeAccountSerializer(stripe_account).data)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filter payments by user"""
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(investor=user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PaymentListSerializer
        return PaymentSerializer
    
    @action(detail=False, methods=['post'])
    def create_investment(self, request):
        """
        Create a payment for investing in an SPV.
        
        POST /api/payments/create_investment/
        {
            "spv_id": 1,
            "amount": 50000,
            "currency": "usd"
        }
        """
        serializer = CreatePaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        spv_id = serializer.validated_data['spv_id']
        amount = serializer.validated_data['amount']
        currency = serializer.validated_data.get('currency', 'usd')
        
        try:
            spv = SPV.objects.get(id=spv_id, status='active')
        except SPV.DoesNotExist:
            return Response({'error': 'SPV not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate minimum investment
        if spv.minimum_lp_investment and amount < spv.minimum_lp_investment:
            return Response({
                'error': f'Minimum investment is ${spv.minimum_lp_investment}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get SPV's Stripe account
        try:
            stripe_account = spv.stripe_account
            if not stripe_account.is_ready_for_payments:
                return Response({
                    'error': 'SPV is not ready to accept payments'
                }, status=status.HTTP_400_BAD_REQUEST)
        except SPVStripeAccount.DoesNotExist:
            return Response({
                'error': 'SPV has not connected their Stripe account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate fees
        platform_fee = int(float(amount) * (PLATFORM_FEE_PERCENTAGE / 100) * 100)  # in cents
        amount_cents = int(float(amount) * 100)
        
        try:
            # Create PaymentIntent with transfer to connected account
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                automatic_payment_methods={'enabled': True},
                application_fee_amount=platform_fee,
                transfer_data={
                    'destination': stripe_account.stripe_account_id,
                },
                metadata={
                    'spv_id': str(spv.id),
                    'spv_name': spv.display_name,
                    'investor_id': str(request.user.id),
                    'investor_email': request.user.email,
                }
            )
            
            # Create Payment record
            payment = Payment.objects.create(
                investor=request.user,
                spv=spv,
                amount=amount,
                currency=currency,
                stripe_payment_intent_id=payment_intent.id,
                client_secret=payment_intent.client_secret,
                status='pending',
                platform_fee=float(platform_fee) / 100,
                platform_fee_percentage=PLATFORM_FEE_PERCENTAGE,
                net_amount=amount - (float(platform_fee) / 100),
                description=f"Investment in {spv.display_name}",
            )
            
            return Response({
                'message': 'Payment created',
                'payment': PaymentSerializer(payment).data,
                'client_secret': payment_intent.client_secret,
            }, status=status.HTTP_201_CREATED)
            
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def create_payment_for_investment(self, request):
        """
        Create Stripe PaymentIntent for an existing pending investment.
        
        This is the preferred flow:
        1. Frontend calls /api/investors/invest/initiate/ to create Investment
        2. Frontend calls this endpoint with the investment_id
        3. Frontend uses client_secret with Stripe.js to complete payment
        4. Webhook updates Investment status on payment success
        
        POST /api/payments/create_payment_for_investment/
        {
            "investment_id": 1
        }
        
        Returns:
        {
            "success": true,
            "client_secret": "pi_xxx_secret_xxx",
            "payment_id": "PAY-XXXXX",
            "amount": 50000
        }
        """
        investment_id = request.data.get('investment_id')
        currency = request.data.get('currency', 'usd')
        
        if not investment_id:
            return Response({
                'success': False,
                'error': 'investment_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get investment - accept both 'approved' and 'pending_payment' status
        try:
            investment = Investment.objects.get(
                id=investment_id,
                investor=request.user,
                status__in=['approved', 'pending_payment']  # Allow approved investments
            )
        except Investment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Investment not found or not approved for payment. Please wait for syndicate approval.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # If status is 'approved', update to 'pending_payment'
        if investment.status == 'approved':
            investment.status = 'pending_payment'
            investment.save(update_fields=['status', 'updated_at'])
        
        spv = investment.spv
        if not spv:
            return Response({
                'success': False,
                'error': 'Investment has no associated SPV'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if payment already exists for this investment
        if investment.payment:
            existing_payment = investment.payment
            if existing_payment.status == 'pending' and existing_payment.stripe_payment_intent_id:
                try:
                    # Check PaymentIntent status with Stripe
                    pi = stripe.PaymentIntent.retrieve(existing_payment.stripe_payment_intent_id)
                    
                    # Only reuse if PaymentIntent is still usable
                    if pi.status in ['requires_payment_method', 'requires_confirmation', 'requires_action']:
                        return Response({
                            'success': True,
                            'message': 'Using existing payment intent',
                            'client_secret': pi.client_secret,  # Use fresh client_secret from Stripe
                            'payment_id': existing_payment.payment_id,
                            'amount': float(existing_payment.amount),
                        })
                    else:
                        # PaymentIntent is in terminal/unusable state - mark old payment as failed
                        existing_payment.status = 'failed' if pi.status == 'canceled' else pi.status
                        existing_payment.save(update_fields=['status', 'updated_at'])
                        investment.payment = None
                        investment.save(update_fields=['payment', 'updated_at'])
                        # Will create new payment below
                except stripe.error.StripeError:
                    # PaymentIntent not found or error - clear and create new
                    existing_payment.status = 'failed'
                    existing_payment.save(update_fields=['status', 'updated_at'])
                    investment.payment = None
                    investment.save(update_fields=['payment', 'updated_at'])
        
        # Get SPV's Stripe account (or use platform account if not connected)
        stripe_account_id = None
        platform_fee = 0
        
        try:
            stripe_account = spv.stripe_account
            if stripe_account.is_ready_for_payments:
                stripe_account_id = stripe_account.stripe_account_id
                platform_fee = int(float(investment.invested_amount) * (PLATFORM_FEE_PERCENTAGE / 100) * 100)
        except SPVStripeAccount.DoesNotExist:
            pass  # Will use platform account directly
        
        amount_cents = int(float(investment.invested_amount) * 100)
        
        try:
            # Build PaymentIntent params
            intent_params = {
                'amount': amount_cents,
                'currency': currency,
                'automatic_payment_methods': {'enabled': True},
                'metadata': {
                    'investment_id': str(investment.id),
                    'spv_id': str(spv.id),
                    'spv_name': spv.display_name,
                    'investor_id': str(request.user.id),
                    'investor_email': request.user.email,
                }
            }
            
            # Add transfer if SPV has connected Stripe
            if stripe_account_id:
                intent_params['application_fee_amount'] = platform_fee
                intent_params['transfer_data'] = {
                    'destination': stripe_account_id,
                }
            
            payment_intent = stripe.PaymentIntent.create(**intent_params)
            
            # Create Payment record
            payment = Payment.objects.create(
                investor=request.user,
                spv=spv,
                investment=investment,
                amount=investment.invested_amount,
                currency=currency,
                stripe_payment_intent_id=payment_intent.id,
                client_secret=payment_intent.client_secret,
                status='pending',
                platform_fee=float(platform_fee) / 100 if platform_fee else 0,
                platform_fee_percentage=PLATFORM_FEE_PERCENTAGE,
                net_amount=float(investment.invested_amount) - (float(platform_fee) / 100) if platform_fee else float(investment.invested_amount),
                description=f"Investment in {spv.display_name}",
            )
            
            # Link payment to investment
            investment.payment = payment
            investment.status = 'payment_processing'
            investment.save(update_fields=['payment', 'status', 'updated_at'])
            
            return Response({
                'success': True,
                'message': 'Payment intent created',
                'client_secret': payment_intent.client_secret,
                'payment_id': payment.payment_id,
                'amount': float(investment.invested_amount),
                'currency': currency,
            }, status=status.HTTP_201_CREATED)
            
        except stripe.error.StripeError as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def confirm(self, request):
        """
        Confirm a payment after successful frontend confirmation.
        
        POST /api/payments/confirm/
        {
            "payment_id": "PAY-XXXXXXXX"
        }
        """
        serializer = ConfirmPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment_id = serializer.validated_data['payment_id']
        
        try:
            payment = Payment.objects.get(payment_id=payment_id, investor=request.user)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check PaymentIntent status
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment.stripe_payment_intent_id)
            
            if payment_intent.status == 'succeeded':
                payment.status = 'succeeded'
                payment.completed_at = timezone.now()
                payment.stripe_charge_id = payment_intent.latest_charge
                payment.save()
                
                # Create Investment record
                self._create_investment_record(payment)
                
                return Response({
                    'message': 'Payment confirmed successfully',
                    'payment': PaymentSerializer(payment).data
                })
            elif payment_intent.status == 'requires_action':
                return Response({
                    'message': 'Payment requires additional action',
                    'requires_action': True,
                    'payment': PaymentSerializer(payment).data
                })
            else:
                payment.status = payment_intent.status
                payment.save()
                return Response({
                    'message': f'Payment status: {payment_intent.status}',
                    'payment': PaymentSerializer(payment).data
                })
                
        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_investment_record(self, payment):
        """Create an Investment record after successful payment"""
        try:
            investment = Investment.objects.create(
                investor=payment.investor,
                spv=payment.spv,
                syndicate_name=payment.spv.display_name,
                sector=payment.spv.company_stage.name if payment.spv.company_stage else None,
                stage=payment.spv.company_stage.name if payment.spv.company_stage else None,
                investment_type='syndicate_deal',
                allocated=payment.spv.allocation or payment.amount,
                raised=payment.amount,
                target=payment.spv.allocation or payment.amount,
                invested_amount=payment.amount,
                min_investment=payment.spv.minimum_lp_investment or 0,
                current_value=payment.amount,
                status='active',
                invested_at=timezone.now(),
            )
            
            # Link payment to investment
            payment.investment = investment
            payment.save()
            
            # Update portfolio
            portfolio, _ = Portfolio.objects.get_or_create(user=payment.investor)
            portfolio.recalculate()
            
        except Exception as e:
            print(f"Error creating investment: {e}")
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get payment statistics.
        
        GET /api/payments/statistics/
        """
        user = request.user
        if user.is_staff:
            payments = Payment.objects.all()
        else:
            payments = Payment.objects.filter(investor=user)
        
        stats = payments.aggregate(
            total_amount=Sum('amount'),
            total_platform_fees=Sum('platform_fee'),
        )
        
        data = {
            'total_payments': payments.count(),
            'total_amount': stats['total_amount'] or 0,
            'successful_payments': payments.filter(status='succeeded').count(),
            'pending_payments': payments.filter(status__in=['pending', 'processing']).count(),
            'failed_payments': payments.filter(status='failed').count(),
            'total_platform_fees': stats['total_platform_fees'] or 0,
        }
        
        return Response(PaymentStatisticsSerializer(data).data)


class StripeWebhookView(APIView):
    """
    Handle Stripe webhook events.
    """
    permission_classes = []  # No auth required for webhooks
    
    @csrf_exempt
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)
        
        # Log the event
        webhook_event, created = PaymentWebhookEvent.objects.get_or_create(
            stripe_event_id=event.id,
            defaults={
                'event_type': event.type,
                'payload': json.loads(payload),
            }
        )
        
        if not created:
            # Already processed
            return HttpResponse(status=200)
        
        try:
            # Handle specific events
            if event.type == 'payment_intent.succeeded':
                self._handle_payment_succeeded(event.data.object)
            elif event.type == 'payment_intent.payment_failed':
                self._handle_payment_failed(event.data.object)
            elif event.type == 'account.updated':
                self._handle_account_updated(event.data.object)
            
            webhook_event.processed = True
            webhook_event.processed_at = timezone.now()
            webhook_event.save()
            
        except Exception as e:
            webhook_event.error = str(e)
            webhook_event.save()
        
        return HttpResponse(status=200)
    
    def _handle_payment_succeeded(self, payment_intent):
        """Handle successful payment - update Investment status and create notification"""
        from investors.dashboard_models import Notification
        
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent.id
            )
            payment.status = 'succeeded'
            payment.completed_at = timezone.now()
            payment.stripe_charge_id = payment_intent.latest_charge
            payment.save()
            
            # Update linked investment if exists
            investment = payment.investment
            if investment:
                investment.status = 'committed'
                investment.commitment_date = timezone.now()
                investment.invested_at = timezone.now()
                investment.save(update_fields=['status', 'commitment_date', 'invested_at', 'updated_at'])
                
                # Calculate ownership percentage
                investment.calculate_ownership()
                
                # Update portfolio
                portfolio, _ = Portfolio.objects.get_or_create(user=payment.investor)
                portfolio.recalculate()
                
                # Create notification
                Notification.objects.create(
                    user=payment.investor,
                    notification_type='investment',
                    title='Investment Confirmed!',
                    message=f'Your investment of ${payment.amount:,.2f} in {investment.syndicate_name} has been confirmed. Thank you for investing!',
                    priority='high',
                    action_required=False,
                    action_url=f'/investments/{investment.id}',
                    action_label='View Investment',
                    related_investment=investment,
                    related_spv=investment.spv,
                )
            elif not payment.investment:
                # Legacy: Create investment if not already created
                self._create_investment_from_payment(payment)
                
        except Payment.DoesNotExist:
            pass
    
    def _create_investment_from_payment(self, payment):
        """Create an Investment record from a payment (legacy flow)"""
        from investors.dashboard_models import Notification
        
        try:
            investment = Investment.objects.create(
                investor=payment.investor,
                spv=payment.spv,
                payment=payment,
                syndicate_name=payment.spv.display_name,
                sector=payment.spv.company_stage.name if payment.spv.company_stage else None,
                stage=payment.spv.company_stage.name if payment.spv.company_stage else None,
                investment_type='syndicate_deal',
                allocated=payment.spv.allocation or payment.amount,
                raised=payment.amount,
                target=payment.spv.allocation or payment.amount,
                invested_amount=payment.amount,
                min_investment=payment.spv.min_investment or 0,
                current_value=payment.amount,
                status='committed',
                invested_at=timezone.now(),
                commitment_date=timezone.now(),
            )
            
            # Link payment to investment
            payment.investment = investment
            payment.save()
            
            # Calculate ownership
            investment.calculate_ownership()
            
            # Update portfolio
            portfolio, _ = Portfolio.objects.get_or_create(user=payment.investor)
            portfolio.recalculate()
            
            # Create notification
            Notification.objects.create(
                user=payment.investor,
                notification_type='investment',
                title='Investment Confirmed!',
                message=f'Your investment of ${payment.amount:,.2f} in {investment.syndicate_name} has been confirmed.',
                priority='high',
                related_investment=investment,
                related_spv=investment.spv,
            )
            
        except Exception as e:
            print(f"Error creating investment from payment: {e}")
    
    def _handle_payment_failed(self, payment_intent):
        """Handle failed payment - update Investment status and notify"""
        from investors.dashboard_models import Notification
        
        try:
            payment = Payment.objects.get(
                stripe_payment_intent_id=payment_intent.id
            )
            payment.status = 'failed'
            if payment_intent.last_payment_error:
                payment.error_code = payment_intent.last_payment_error.code
                payment.error_message = payment_intent.last_payment_error.message
            payment.save()
            
            # Update linked investment
            if payment.investment:
                investment = payment.investment
                investment.status = 'failed'
                investment.save(update_fields=['status', 'updated_at'])
                
                # Create notification
                Notification.objects.create(
                    user=payment.investor,
                    notification_type='investment',
                    title='Payment Failed',
                    message=f'Your payment of ${payment.amount:,.2f} for {investment.syndicate_name} failed. Please try again.',
                    priority='urgent',
                    action_required=True,
                    action_url=f'/investments/{investment.id}/pay',
                    action_label='Retry Payment',
                    related_investment=investment,
                    related_spv=investment.spv,
                )
                
        except Payment.DoesNotExist:
            pass
    
    def _handle_account_updated(self, account):
        """Handle Stripe Connect account updates"""
        try:
            stripe_account = SPVStripeAccount.objects.get(
                stripe_account_id=account.id
            )
            stripe_account.charges_enabled = account.charges_enabled
            stripe_account.payouts_enabled = account.payouts_enabled
            stripe_account.details_submitted = account.details_submitted
            
            if account.details_submitted:
                stripe_account.account_status = 'active'
            
            stripe_account.save()
        except SPVStripeAccount.DoesNotExist:
            pass

