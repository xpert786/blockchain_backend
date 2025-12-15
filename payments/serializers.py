from rest_framework import serializers
from .models import SPVStripeAccount, Payment, PaymentWebhookEvent
from spv.models import SPV


class SPVStripeAccountSerializer(serializers.ModelSerializer):
    """Serializer for SPV Stripe Account"""
    
    spv_detail = serializers.SerializerMethodField()
    is_ready_for_payments = serializers.ReadOnlyField()
    
    class Meta:
        model = SPVStripeAccount
        fields = [
            'id',
            'spv',
            'spv_detail',
            'stripe_account_id',
            'account_status',
            'charges_enabled',
            'payouts_enabled',
            'details_submitted',
            'is_ready_for_payments',
            'onboarding_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'stripe_account_id', 'account_status',
            'charges_enabled', 'payouts_enabled', 'details_submitted',
            'onboarding_url', 'created_at', 'updated_at'
        ]
    
    def get_spv_detail(self, obj):
        return {
            'id': obj.spv.id,
            'display_name': obj.spv.display_name,
            'status': obj.spv.status,
        }


class StripeConnectOnboardingSerializer(serializers.Serializer):
    """Serializer for initiating Stripe Connect onboarding"""
    
    spv_id = serializers.IntegerField(help_text="SPV ID to connect Stripe account")
    return_url = serializers.URLField(
        required=False,
        help_text="URL to redirect after onboarding success"
    )
    refresh_url = serializers.URLField(
        required=False,
        help_text="URL to redirect if onboarding link expires"
    )


class CreatePaymentSerializer(serializers.Serializer):
    """Serializer for creating a new payment/investment"""
    
    spv_id = serializers.IntegerField(help_text="SPV ID to invest in")
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=1,
        help_text="Investment amount"
    )
    payment_method_id = serializers.CharField(
        required=False,
        help_text="Stripe PaymentMethod ID (pm_xxx) if already collected"
    )
    currency = serializers.CharField(
        default='usd',
        help_text="Currency code"
    )
    
    def validate_spv_id(self, value):
        try:
            spv = SPV.objects.get(id=value, status='active')
        except SPV.DoesNotExist:
            raise serializers.ValidationError("SPV not found or not active")
        
        # Check if SPV has connected Stripe account
        if not hasattr(spv, 'stripe_account') or not spv.stripe_account.is_ready_for_payments:
            raise serializers.ValidationError("SPV is not set up to receive payments")
        
        return value
    
    def validate_amount(self, value):
        # Will validate against SPV minimum investment in view
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    investor_detail = serializers.SerializerMethodField()
    spv_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'payment_id',
            'investor',
            'investor_detail',
            'spv',
            'spv_detail',
            'investment',
            'amount',
            'currency',
            'status',
            'payment_method',
            'platform_fee',
            'stripe_fee',
            'net_amount',
            'client_secret',
            'description',
            'error_code',
            'error_message',
            'created_at',
            'completed_at',
        ]
        read_only_fields = [
            'id', 'payment_id', 'status', 'platform_fee', 'stripe_fee',
            'net_amount', 'client_secret', 'error_code', 'error_message',
            'created_at', 'completed_at'
        ]
    
    def get_investor_detail(self, obj):
        return {
            'id': obj.investor.id,
            'username': obj.investor.username,
            'email': obj.investor.email,
        }
    
    def get_spv_detail(self, obj):
        return {
            'id': obj.spv.id,
            'display_name': obj.spv.display_name,
        }


class PaymentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for payment lists"""
    
    spv_name = serializers.CharField(source='spv.display_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id',
            'payment_id',
            'spv_name',
            'amount',
            'currency',
            'status',
            'payment_method',
            'created_at',
        ]


class ConfirmPaymentSerializer(serializers.Serializer):
    """Serializer for confirming a payment after 3D Secure"""
    
    payment_id = serializers.CharField(help_text="Payment ID (PAY-xxx)")
    payment_intent_id = serializers.CharField(
        required=False,
        help_text="Stripe PaymentIntent ID for confirmation"
    )


class PaymentStatisticsSerializer(serializers.Serializer):
    """Serializer for payment statistics"""
    
    total_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    successful_payments = serializers.IntegerField()
    pending_payments = serializers.IntegerField()
    failed_payments = serializers.IntegerField()
    total_platform_fees = serializers.DecimalField(max_digits=20, decimal_places=2)
