"""
Investment Flow Views - Complete investor investment flow with Stripe integration.

This module provides APIs for:
1. Get SPV investment details for investment decision
2. Initiate investment (create pending payment record)
3. List investor's investments
4. Cancel pending investment
5. Get investment status
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Sum
from decimal import Decimal

from spv.models import SPV
from users.models import CustomUser
from .dashboard_models import Investment, Portfolio, Notification, KYCStatus
from .models import InvestorProfile


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_investment_details(request, spv_id):
    """
    Get SPV details for investment decision.
    
    GET /api/investors/invest/spv/{spv_id}/details/
    
    Returns SPV information needed to make investment decision:
    - Basic SPV info
    - Investment terms (min, max, allocation)
    - Current raise status
    - Investor's eligibility status
    """
    try:
        spv = SPV.objects.select_related('company_stage', 'round', 'created_by').get(id=spv_id)
    except SPV.DoesNotExist:
        return Response({
            'success': False,
            'error': 'SPV not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if SPV is open for investment
    if spv.status not in ['active', 'approved']:
        return Response({
            'success': False,
            'error': 'This SPV is not currently open for investment'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    # Get investor's KYC status
    kyc_verified = False
    try:
        kyc_status = KYCStatus.objects.get(user=user)
        kyc_verified = kyc_status.status == 'verified'
    except KYCStatus.DoesNotExist:
        pass
    
    # Get investor's accreditation status
    accredited = False
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
        accredited = investor_profile.is_accredited_investor
    except InvestorProfile.DoesNotExist:
        pass
    
    # Calculate remaining allocation
    total_invested = Investment.objects.filter(
        spv=spv,
        status__in=['committed', 'active', 'completed']
    ).aggregate(total=models.Sum('invested_amount'))['total'] or Decimal('0')
    
    remaining_allocation = (spv.allocation or Decimal('0')) - total_invested
    
    # Check if user already has a pending or active investment
    existing_investment = Investment.objects.filter(
        investor=user,
        spv=spv,
        status__in=['pending_payment', 'payment_processing', 'committed', 'active']
    ).first()
    
    response_data = {
        'success': True,
        'spv': {
            'id': spv.id,
            'display_name': spv.display_name,
            'description': getattr(spv, 'deal_memo', None) or spv.display_name,
            'status': spv.status,
            'sector': spv.deal_tags[0] if spv.deal_tags else None,
            'stage': spv.company_stage.name if spv.company_stage else None,
            'lead_name': f"{spv.created_by.first_name} {spv.created_by.last_name}".strip() or spv.created_by.username if spv.created_by else None,
        },
        'investment_terms': {
            'min_investment': float(spv.minimum_lp_investment or 0),
            'allocation': float(spv.allocation or 0),
            'remaining_allocation': float(remaining_allocation),
            'round_size': float(spv.round_size or 0),
            'total_invested': float(total_invested),
            'carry_percentage': float(spv.total_carry_percentage or 0),
            'management_fee_percentage': 0,
        },
        'deadline': {
            'target_closing_date': str(spv.target_closing_date) if spv.target_closing_date else None,
            'days_left': (spv.target_closing_date - timezone.now().date()).days if spv.target_closing_date else None,
        },
        'investor_status': {
            'kyc_verified': kyc_verified,
            'accredited': accredited,
            'can_invest': kyc_verified,
            'existing_investment': {
                'id': existing_investment.id,
                'amount': float(existing_investment.invested_amount),
                'status': existing_investment.status,
            } if existing_investment else None,
        }
    }
    
    return Response(response_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_investment(request):
    """
    Create investment commitment (pending payment).
    
    POST /api/investors/invest/initiate/
    
    Payload:
    {
        "spv_id": 1,
        "amount": 50000,
        "investment_type": "syndicate_deal"  // optional
    }
    
    Validations:
    - User is KYC verified
    - User is accredited (if required by SPV)
    - Amount >= min_investment
    - Amount <= remaining allocation
    - SPV is open for investment
    """
    spv_id = request.data.get('spv_id')
    amount = request.data.get('amount')
    investment_type = request.data.get('investment_type', 'syndicate_deal')
    
    # Validate required fields
    if not spv_id:
        return Response({
            'success': False,
            'error': 'spv_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not amount:
        return Response({
            'success': False,
            'error': 'amount is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        amount = Decimal(str(amount))
    except:
        return Response({
            'success': False,
            'error': 'Invalid amount format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get SPV
    try:
        spv = SPV.objects.get(id=spv_id)
    except SPV.DoesNotExist:
        return Response({
            'success': False,
            'error': 'SPV not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Validate SPV is open for investment
    if spv.status not in ['active', 'approved']:
        return Response({
            'success': False,
            'error': 'This SPV is not currently open for investment'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    
    # Validate KYC
    kyc_verified = False
    try:
        kyc_status = KYCStatus.objects.get(user=user)
        kyc_verified = kyc_status.status == 'verified'
    except KYCStatus.DoesNotExist:
        pass
    
    if not kyc_verified:
        return Response({
            'success': False,
            'error': 'KYC verification required before investing',
            'error_code': 'KYC_REQUIRED'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Validate accreditation if required (check if field exists)
    require_accreditation = getattr(spv, 'require_accreditation', False)
    if require_accreditation:
        try:
            investor_profile = InvestorProfile.objects.get(user=user)
            if not investor_profile.is_accredited_investor:
                return Response({
                    'success': False,
                    'error': 'This SPV requires accredited investor status',
                    'error_code': 'ACCREDITATION_REQUIRED'
                }, status=status.HTTP_403_FORBIDDEN)
        except InvestorProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Investor profile not found. Please complete your profile.',
                'error_code': 'PROFILE_REQUIRED'
            }, status=status.HTTP_403_FORBIDDEN)
    
    # Validate minimum investment
    min_investment = spv.minimum_lp_investment or Decimal('0')
    if min_investment and amount < min_investment:
        return Response({
            'success': False,
            'error': f'Minimum investment is ${min_investment:,.2f}',
            'error_code': 'BELOW_MINIMUM'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate remaining allocation
    from django.db.models import Sum
    total_invested = Investment.objects.filter(
        spv=spv,
        status__in=['committed', 'active', 'completed', 'pending_payment', 'payment_processing']
    ).aggregate(total=Sum('invested_amount'))['total'] or Decimal('0')
    
    remaining_allocation = (spv.allocation or Decimal('0')) - total_invested
    
    if amount > remaining_allocation:
        return Response({
            'success': False,
            'error': f'Amount exceeds remaining allocation (${remaining_allocation:,.2f} available)',
            'error_code': 'EXCEEDS_ALLOCATION'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check for existing pending investment
    existing_investment = Investment.objects.filter(
        investor=user,
        spv=spv,
        status__in=['pending_payment', 'payment_processing']
    ).first()
    
    if existing_investment:
        return Response({
            'success': False,
            'error': 'You already have a pending investment for this SPV',
            'error_code': 'PENDING_EXISTS',
            'existing_investment_id': existing_investment.id
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Create investment record
    with transaction.atomic():
        investment = Investment.objects.create(
            investor=user,
            spv=spv,
            syndicate_name=spv.display_name,
            sector=spv.deal_tags[0] if spv.deal_tags else None,
            stage=spv.company_stage.name if spv.company_stage else None,
            investment_type=investment_type,
            invested_amount=amount,
            current_value=amount,
            allocated=spv.allocation or 0,
            raised=total_invested,
            target=spv.round_size or 0,
            min_investment=spv.minimum_lp_investment or 0,
            status='pending_payment',
            deadline=spv.target_closing_date,
            days_left=(spv.target_closing_date - timezone.now().date()).days if spv.target_closing_date else 0,
        )
        
        # Create notification
        Notification.objects.create(
            user=user,
            notification_type='investment',
            title='Investment Initiated',
            message=f'Your investment of ${amount:,.2f} in {spv.display_name} has been initiated. Please complete payment to confirm.',
            priority='high',
            action_required=True,
            action_url=f'/investments/{investment.id}/pay',
            action_label='Complete Payment',
            related_investment=investment,
            related_spv=spv,
        )
    
    return Response({
        'success': True,
        'message': 'Investment initiated successfully. Please complete payment.',
        'investment': {
            'id': investment.id,
            'spv_id': spv.id,
            'spv_name': spv.display_name,
            'amount': float(amount),
            'status': investment.status,
            'status_display': investment.get_status_display(),
            'created_at': investment.created_at.isoformat(),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_investments(request):
    """
    List all investments for current investor.
    
    GET /api/investors/invest/my-investments/
    
    Query params:
    - status: Filter by status (pending_payment, committed, active, etc.)
    - spv_id: Filter by SPV
    """
    user = request.user
    queryset = Investment.objects.filter(investor=user).select_related('spv', 'payment')
    
    # Apply filters
    status_filter = request.query_params.get('status')
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    spv_id = request.query_params.get('spv_id')
    if spv_id:
        queryset = queryset.filter(spv_id=spv_id)
    
    investments = []
    for inv in queryset:
        investments.append({
            'id': inv.id,
            'spv_id': inv.spv.id if inv.spv else None,
            'spv_name': inv.syndicate_name,
            'sector': inv.sector,
            'stage': inv.stage,
            'invested_amount': float(inv.invested_amount),
            'current_value': float(inv.current_value),
            'ownership_percentage': float(inv.ownership_percentage),
            'status': inv.status,
            'status_display': inv.get_status_display(),
            'payment_id': inv.payment.payment_id if inv.payment else None,
            'created_at': inv.created_at.isoformat(),
            'commitment_date': inv.commitment_date.isoformat() if inv.commitment_date else None,
            'gain_loss': float(inv.gain_loss),
            'gain_loss_percentage': float(inv.gain_loss_percentage),
        })
    
    return Response({
        'success': True,
        'count': len(investments),
        'investments': investments
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def investment_detail(request, investment_id):
    """
    Get single investment details.
    
    GET /api/investors/invest/{investment_id}/
    """
    user = request.user
    
    try:
        investment = Investment.objects.select_related('spv', 'payment').get(
            id=investment_id,
            investor=user
        )
    except Investment.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Investment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'investment': {
            'id': investment.id,
            'spv': {
                'id': investment.spv.id if investment.spv else None,
                'display_name': investment.syndicate_name,
                'status': investment.spv.status if investment.spv else None,
            },
            'sector': investment.sector,
            'stage': investment.stage,
            'investment_type': investment.investment_type,
            'invested_amount': float(investment.invested_amount),
            'current_value': float(investment.current_value),
            'ownership_percentage': float(investment.ownership_percentage),
            'status': investment.status,
            'status_display': investment.get_status_display(),
            'payment': {
                'id': investment.payment.id,
                'payment_id': investment.payment.payment_id,
                'status': investment.payment.status,
                'stripe_payment_intent_id': investment.payment.stripe_payment_intent_id,
            } if investment.payment else None,
            'created_at': investment.created_at.isoformat(),
            'commitment_date': investment.commitment_date.isoformat() if investment.commitment_date else None,
            'invested_at': investment.invested_at.isoformat() if investment.invested_at else None,
            'deadline': str(investment.deadline) if investment.deadline else None,
            'days_left': investment.days_left,
            'gain_loss': float(investment.gain_loss),
            'gain_loss_percentage': float(investment.gain_loss_percentage),
        }
    })


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def cancel_investment(request, investment_id):
    """
    Cancel a pending investment (before payment).
    
    PATCH /api/investors/invest/{investment_id}/cancel/
    
    Only investments with status 'pending_payment' can be cancelled.
    """
    user = request.user
    
    try:
        investment = Investment.objects.get(id=investment_id, investor=user)
    except Investment.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Investment not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if investment.status != 'pending_payment':
        return Response({
            'success': False,
            'error': f'Cannot cancel investment with status: {investment.get_status_display()}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    with transaction.atomic():
        investment.status = 'cancelled'
        investment.save(update_fields=['status', 'updated_at'])
        
        # Create notification
        Notification.objects.create(
            user=user,
            notification_type='investment',
            title='Investment Cancelled',
            message=f'Your investment of ${investment.invested_amount:,.2f} in {investment.syndicate_name} has been cancelled.',
            priority='normal',
            related_investment=investment,
            related_spv=investment.spv,
        )
    
    return Response({
        'success': True,
        'message': 'Investment cancelled successfully',
        'investment_id': investment.id,
        'status': investment.status
    })
