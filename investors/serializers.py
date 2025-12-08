from rest_framework import serializers
from .models import InvestorProfile
from users.models import CustomUser
import json
import os
from django.conf import settings


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
            'national_id',
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
            # Step 3.5: Jurisdiction-Aware Accreditation Check
            'accreditation_jurisdiction',
            'accreditation_rules_selected',
            'accreditation_check_completed',
            'accreditation_check_completed_at',
            # Step 4: Accreditation (If Applicable)
            'investor_type',
            'full_legal_name',
            'legal_place_of_residence',
            'accreditation_method',
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
            'national_id',
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
            'national_id',
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
    
    government_id_url = serializers.SerializerMethodField(read_only=True)
    has_government_id = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = InvestorProfile
        fields = [
            'government_id',
            'government_id_url',
            'has_government_id',
            'date_of_birth',
            'street_address',
            'city',
            'state_province',
            'zip_postal_code',
            'country',
        ]
    
    def get_government_id_url(self, obj):
        """Get government ID file URL"""
        if obj.government_id:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.government_id.url)
            return obj.government_id.url
        return None
    
    def get_has_government_id(self, obj):
        """Check if government ID is uploaded"""
        return bool(obj.government_id)
    
    def validate(self, data):
        """Validate Step 2 fields"""
        # Only require government_id if not already uploaded AND instance exists
        if self.instance:
            # On PATCH/update, allow skipping file if already uploaded
            if not data.get('government_id') and not self.instance.government_id:
                raise serializers.ValidationError({"government_id": "Government ID is required"})
        else:
            # On create, require the file
            if not data.get('government_id'):
                raise serializers.ValidationError({"government_id": "Government ID is required"})
        
        # Validate other required fields only if not already set
        if self.instance:
            if not data.get('date_of_birth') and not self.instance.date_of_birth:
                raise serializers.ValidationError({"date_of_birth": "Date of birth is required"})
            if not data.get('street_address') and not self.instance.street_address:
                raise serializers.ValidationError({"street_address": "Street address is required"})
        return data


class InvestorProfileStep3Serializer(serializers.ModelSerializer):
    """Serializer for Step 3: Bank Details / Payment Setup"""
    
    proof_of_bank_ownership_url = serializers.SerializerMethodField(read_only=True)
    has_proof_of_bank_ownership = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = InvestorProfile
        fields = [
            'bank_account_number',
            'bank_name',
            'account_holder_name',
            'swift_ifsc_code',
            'proof_of_bank_ownership',
            'proof_of_bank_ownership_url',
            'has_proof_of_bank_ownership',
        ]
    
    def get_proof_of_bank_ownership_url(self, obj):
        """Get bank proof file URL"""
        if obj.proof_of_bank_ownership:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.proof_of_bank_ownership.url)
            return obj.proof_of_bank_ownership.url
        return None
    
    def get_has_proof_of_bank_ownership(self, obj):
        """Check if bank proof is uploaded"""
        return bool(obj.proof_of_bank_ownership)
    
    def validate(self, data):
        """Validate Step 3 fields"""
        # On PATCH/update, allow skipping fields if already set
        if self.instance:
            # Only require proof if not already uploaded
            if not data.get('proof_of_bank_ownership') and not self.instance.proof_of_bank_ownership:
                raise serializers.ValidationError({"proof_of_bank_ownership": "Bank ownership proof is required"})
            if not data.get('bank_account_number') and not self.instance.bank_account_number:
                raise serializers.ValidationError({"bank_account_number": "Bank account number is required"})
            if not data.get('bank_name') and not self.instance.bank_name:
                raise serializers.ValidationError({"bank_name": "Bank name is required"})
            if not data.get('account_holder_name') and not self.instance.account_holder_name:
                raise serializers.ValidationError({"account_holder_name": "Account holder name is required"})
        return data


class InvestorProfileAccreditationCheckSerializer(serializers.ModelSerializer):
    """Serializer for Jurisdiction-Aware Accreditation Check (New Screen before Step 4)"""
    
    class Meta:
        model = InvestorProfile
        fields = [
            'accreditation_jurisdiction',
            'accreditation_rules_selected',
            'accreditation_check_completed',
            'accreditation_check_completed_at',
        ]
    
    def validate_accreditation_rules_selected(self, value):
        """Validate that at least one rule is selected"""
        if not isinstance(value, list):
            raise serializers.ValidationError("accreditation_rules_selected must be a list")
        # Ensure items are strings (we expect clients to submit textual rules)
        for item in value:
            if not isinstance(item, str):
                raise serializers.ValidationError("Each accreditation rule must be a string matching the rule text")

        # Do not enforce non-empty here; the overall validate() will require
        # at least one rule when the user marks the check as completed.
        return value
    
    def validate(self, data):
        """Validate that jurisdiction is provided when completing the check"""
        if data.get('accreditation_check_completed'):
            if not data.get('accreditation_jurisdiction'):
                raise serializers.ValidationError({
                    "accreditation_jurisdiction": "Jurisdiction is required when completing accreditation check"
                })
            if not data.get('accreditation_rules_selected'):
                raise serializers.ValidationError({
                    "accreditation_rules_selected": "At least one accreditation rule must be selected"
                })

            # Validate that selected rules exist in the jurisdiction rules JSON
            try:
                rules_file = os.path.join(settings.BASE_DIR, 'accreditation_rules.json')
                with open(rules_file, 'r', encoding='utf-8') as f:
                    all_rules = json.load(f)
            except Exception:
                # If we cannot load the file, skip strict validation
                all_rules = {}

            jurisdiction = (data.get('accreditation_jurisdiction') or '').lower()
            jurisdiction_rules = all_rules.get(jurisdiction) or all_rules.get('default') or {}

            # Build allowed rule texts from natural_person_rules and entity_rules if present
            allowed = set()
            if isinstance(jurisdiction_rules, dict):
                npr = jurisdiction_rules.get('natural_person_rules') or []
                er = jurisdiction_rules.get('entity_rules') or []
                for r in npr:
                    if isinstance(r, str):
                        allowed.add(r.strip())
                for r in er:
                    if isinstance(r, str):
                        allowed.add(r.strip())

            # If allowed set is empty, we can't validate strictly
            if allowed:
                invalid = [s for s in data.get('accreditation_rules_selected', []) if s.strip() not in allowed]
                if invalid:
                    raise serializers.ValidationError({
                        'accreditation_rules_selected': f"Invalid rule(s) for jurisdiction '{jurisdiction}': {invalid}"
                    })
        return data


class InvestorProfileStep4Serializer(serializers.ModelSerializer):
    """Serializer for Step 4: Accreditation (If Applicable)"""
    
    proof_of_income_net_worth_url = serializers.SerializerMethodField(read_only=True)
    has_proof_of_income_net_worth = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = InvestorProfile
        fields = [
            'investor_type',
            'full_legal_name',
            'legal_place_of_residence',
            'accreditation_method',
            'proof_of_income_net_worth',
            'proof_of_income_net_worth_url',
            'has_proof_of_income_net_worth',
            'is_accredited_investor',
            'meets_local_investment_thresholds',
        ]
    
    def get_proof_of_income_net_worth_url(self, obj):
        """Get income/net worth proof file URL"""
        if obj.proof_of_income_net_worth:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.proof_of_income_net_worth.url)
            return obj.proof_of_income_net_worth.url
        return None
    
    def get_has_proof_of_income_net_worth(self, obj):
        """Check if proof is uploaded"""
        return bool(obj.proof_of_income_net_worth)
    
    def validate(self, data):
        """Validate Step 4 fields - Optional step"""
        # On PATCH/update, allow skipping file if already set
        if self.instance:
            # If user claims to be accredited, require proof (only if not already uploaded)
            if data.get('is_accredited_investor'):
                if not data.get('proof_of_income_net_worth') and not self.instance.proof_of_income_net_worth:
                    raise serializers.ValidationError({
                        "proof_of_income_net_worth": "Proof of income or net worth is required for accredited investors"
                    })
        else:
            # On create, require proof if claiming to be accredited
            if data.get('is_accredited_investor') and not data.get('proof_of_income_net_worth'):
                raise serializers.ValidationError({
                    "proof_of_income_net_worth": "Proof of income or net worth is required for accredited investors"
                })
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




class InvestorOnboardingProgressSerializer(serializers.ModelSerializer):
    """
    Serializer to power the 'You're Almost Ready!' progress UI.
    Returns boolean status for each verification step.
    """
    email_verified = serializers.SerializerMethodField()
    phone_verified = serializers.SerializerMethodField()
    accredited_verified = serializers.SerializerMethodField()
    kyc_completed = serializers.SerializerMethodField()
    tax_forms_completed = serializers.SerializerMethodField()
    
    # helper to calculate overall percentage if needed
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = InvestorProfile
        fields = [
            'email_verified',
            'phone_verified',
            'accredited_verified',
            'kyc_completed',
            'tax_forms_completed',
            'completion_percentage',
        ]

    def get_email_verified(self, obj):
        # Check the CustomUser model's email_verified field
        return obj.user.email_verified

    def get_phone_verified(self, obj):
        # Check the CustomUser model's phone_verified field
        return obj.user.phone_verified

    def get_accredited_verified(self, obj):
        # Directly from your model field
        return obj.is_accredited_investor

    def get_kyc_completed(self, obj):
        # Reusing the logic you already wrote in the model's @property
        # This checks government_id, DOB, and address fields
        return obj.step2_completed

    def get_tax_forms_completed(self, obj):
        # Checks if W9 is submitted and TIN is present
        return bool(obj.w9_form_submitted and obj.tax_identification_number)

    def get_completion_percentage(self, obj):
        steps = [
            self.get_email_verified(obj),
            self.get_phone_verified(obj),
            self.get_accredited_verified(obj),
            self.get_kyc_completed(obj),
            self.get_tax_forms_completed(obj)
        ]
        completed = sum(steps)
        return int((completed / len(steps)) * 100)