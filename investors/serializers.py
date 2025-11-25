from rest_framework import serializers
from .models import InvestorProfile
from users.models import CustomUser


class InvestorProfileSerializer(serializers.ModelSerializer):
    """Serializer for complete InvestorProfile model"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    current_step = serializers.ReadOnlyField()
    step1_completed = serializers.ReadOnlyField()
    step2_completed = serializers.ReadOnlyField()
    step3_completed = serializers.ReadOnlyField()
    step4_completed = serializers.ReadOnlyField()
    step5_completed = serializers.ReadOnlyField()
    step6_completed = serializers.ReadOnlyField()
    
    class Meta:
        model = InvestorProfile
        fields = [
            'id',
            'user',
            'user_email',
            'user_username',
            # Step 1: Basic Information
            'full_name',
            'email_address',
            'phone_number',
            'country_of_residence',
            # Step 2: KYC / Identity Verification
            'government_id',
            'date_of_birth',
            'street_address',
            'city',
            'state_province',
            'zip_postal_code',
            'country',
            # Step 3: Bank Details / Payment Setup
            'bank_account_number',
            'bank_name',
            'account_holder_name',
            'swift_ifsc_code',
            'proof_of_bank_ownership',
            # Step 4: Accreditation (If Applicable)
            'proof_of_income_net_worth',
            'is_accredited_investor',
            'meets_local_investment_thresholds',
            # Step 5: Accept Agreements
            'terms_and_conditions_accepted',
            'risk_disclosure_accepted',
            'privacy_policy_accepted',
            'confirmation_of_true_information',
            # Application Status
            'application_status',
            'application_submitted',
            'submitted_at',
            # Progress tracking
            'current_step',
            'step1_completed',
            'step2_completed',
            'step3_completed',
            'step4_completed',
            'step5_completed',
            'step6_completed',
            # Timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'submitted_at']
    


class InvestorProfileCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating an InvestorProfile"""
    
    class Meta:
        model = InvestorProfile
        fields = [
            'full_name',
            'email_address',
            'phone_number',
            'country_of_residence',
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        
        # Check if profile already exists
        if hasattr(user, 'investor_profile'):
            raise serializers.ValidationError("Investor profile already exists for this user")
        
        validated_data['user'] = user
        return super().create(validated_data)


class InvestorProfileStep1Serializer(serializers.ModelSerializer):
    """Serializer for Step 1: Basic Information"""
    
    class Meta:
        model = InvestorProfile
        fields = [
            'full_name',
            'email_address',
            'phone_number',
            'country_of_residence',
        ]
    
    def validate(self, data):
        """Validate Step 1 fields"""
        if not data.get('full_name'):
            raise serializers.ValidationError("Full name is required")
        if not data.get('email_address'):
            raise serializers.ValidationError("Email address is required")
        if not data.get('phone_number'):
            raise serializers.ValidationError("Phone number is required")
        return data


class InvestorProfileStep2Serializer(serializers.ModelSerializer):
    """Serializer for Step 2: KYC / Identity Verification"""
    
    class Meta:
        model = InvestorProfile
        fields = [
            'government_id',
            'date_of_birth',
            'street_address',
            'city',
            'state_province',
            'zip_postal_code',
            'country',
        ]
    
    def validate(self, data):
        """Validate Step 2 fields"""
        if not data.get('government_id'):
            raise serializers.ValidationError("Government ID is required")
        if not data.get('date_of_birth'):
            raise serializers.ValidationError("Date of birth is required")
        if not data.get('street_address'):
            raise serializers.ValidationError("Street address is required")
        return data


class InvestorProfileStep3Serializer(serializers.ModelSerializer):
    """Serializer for Step 3: Bank Details / Payment Setup"""
    
    class Meta:
        model = InvestorProfile
        fields = [
            'bank_account_number',
            'bank_name',
            'account_holder_name',
            'swift_ifsc_code',
            'proof_of_bank_ownership',
        ]
    
    def validate(self, data):
        """Validate Step 3 fields"""
        if not data.get('bank_account_number'):
            raise serializers.ValidationError("Bank account number is required")
        if not data.get('bank_name'):
            raise serializers.ValidationError("Bank name is required")
        if not data.get('account_holder_name'):
            raise serializers.ValidationError("Account holder name is required")
        return data


class InvestorProfileStep4Serializer(serializers.ModelSerializer):
    """Serializer for Step 4: Accreditation (If Applicable)"""
    
    class Meta:
        model = InvestorProfile
        fields = [
            'proof_of_income_net_worth',
            'is_accredited_investor',
            'meets_local_investment_thresholds',
        ]
    
    def validate(self, data):
        """Validate Step 4 fields - Optional step"""
        # If user claims to be accredited, require proof
        if data.get('is_accredited_investor') and not data.get('proof_of_income_net_worth'):
            raise serializers.ValidationError("Proof of income or net worth is required for accredited investors")
        return data


class InvestorProfileStep5Serializer(serializers.ModelSerializer):
    """Serializer for Step 5: Accept Agreements"""
    
    class Meta:
        model = InvestorProfile
        fields = [
            'terms_and_conditions_accepted',
            'risk_disclosure_accepted',
            'privacy_policy_accepted',
            'confirmation_of_true_information',
        ]
    
    def validate(self, data):
        """Validate that all agreements are accepted"""
        required_agreements = [
            'terms_and_conditions_accepted',
            'risk_disclosure_accepted',
            'privacy_policy_accepted',
            'confirmation_of_true_information'
        ]
        
        for agreement in required_agreements:
            if not data.get(agreement, False):
                raise serializers.ValidationError(f"You must accept: {agreement}")
        
        return data


class InvestorProfileStep6Serializer(serializers.ModelSerializer):
    """Serializer for Step 6: Final Review - Read-only display"""
    
    class Meta:
        model = InvestorProfile
        fields = '__all__'
        read_only_fields = '__all__'


class InvestorProfileSubmitSerializer(serializers.ModelSerializer):
    """Serializer for submitting the application"""
    
    class Meta:
        model = InvestorProfile
        fields = ['application_submitted', 'submitted_at', 'application_status']
        read_only_fields = ['submitted_at', 'application_status']
    
    def validate(self, data):
        """Validate that all required steps are completed before submission"""
        profile = self.instance
        
        if not profile.step1_completed:
            raise serializers.ValidationError("Please complete Step 1: Basic Information")
        
        if not profile.step2_completed:
            raise serializers.ValidationError("Please complete Step 2: KYC / Identity Verification")
        
        if not profile.step3_completed:
            raise serializers.ValidationError("Please complete Step 3: Bank Details / Payment Setup")
        
        if not profile.step5_completed:
            raise serializers.ValidationError("Please complete Step 5: Accept Agreements")
        
        return data
