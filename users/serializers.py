from rest_framework import serializers
from .models import CustomUser, Sector, Geography, EmailVerification, TwoFactorAuth, TermsAcceptance, SyndicateProfile, TeamMember, ComplianceDocument, FeeRecipient, CreditCard, BankAccount, BeneficialOwner
from .email_utils import send_verification_email, send_sms_verification
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import random
import string
from .sms_utils import send_twilio_sms
from investors.models import InvestorProfile
import os
import json
from django.conf import settings

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for CustomUser model"""
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 
                  'password', 'is_active', 'is_staff', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        """Create a new user with encrypted password"""
        password = validated_data.pop('password', None)
        user = CustomUser.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user, handling password separately"""
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'phone_number', 'role', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        # Split full name into first and last name
        full_name = validated_data.pop('full_name')
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        validated_data.pop('password2')
        password = validated_data.pop('password')
        # Remove email from validated_data so it's not passed twice
        email = validated_data.pop('email', None)

        user = CustomUser.objects.create(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user


class SectorSerializer(serializers.ModelSerializer):
    """Serializer for Sector model"""
    
    class Meta:
        model = Sector
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class GeographySerializer(serializers.ModelSerializer):
    """Serializer for Geography model"""
    
    class Meta:
        model = Geography
        fields = ['id', 'name', 'region', 'country_code', 'created_at']
        read_only_fields = ['id', 'created_at']


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with full details"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = CustomUser
        fields = ['full_name', 'email', 'phone_number', 'role', 'password', 'confirm_password']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Check if email already exists
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        
        return attrs
    
    def create(self, validated_data):
        # Split full name into first and last name
        full_name = validated_data.pop('full_name')
        name_parts = full_name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        # Generate username from email (part before @)
        # Pop email so it is not passed twice in **validated_data
        email = validated_data.pop('email')
        base_username = email.split('@')[0]
        username = base_username
        
        # Ensure username is unique
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = CustomUser.objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            **validated_data
        )
        user.set_password(password)
        user.save()
        
        return user


class EmailVerificationSerializer(serializers.ModelSerializer):
    """Serializer for email verification"""
    
    class Meta:
        model = EmailVerification
        fields = ['email', 'code']
    
    def create(self, validated_data):
        user = self.context['user']
        email = validated_data['email']
        
        # Generate 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
        # Set expiration time (15 minutes from now)
        expires_at = timezone.now() + timedelta(minutes=15)
        
        # Create or update verification record
        verification, created = EmailVerification.objects.update_or_create(
            user=user,
            email=email,
            defaults={
                'code': code,
                'is_verified': False,
                'expires_at': expires_at
            }
        )
        
        # Send email with verification code
        send_verification_email(email, code, user.first_name)
        
        return verification


class TwoFactorAuthSerializer(serializers.ModelSerializer):
    """Serializer for two-factor authentication"""
    
    # Make code optional/read-only so it's not required in input
    code = serializers.CharField(required=False, read_only=True)
    
    class Meta:
        model = TwoFactorAuth
        fields = ['phone_number', 'code']
        read_only_fields = ['code']
    
    def create(self, validated_data):
        user = self.context['user']
        phone_number = validated_data['phone_number']
        
        # Generate 6-digit code
        code = ''.join(random.choices(string.digits, k=4))
        
        # Set expiration time (10 minutes from now)
        expires_at = timezone.now() + timedelta(minutes=10)
        
        # Create or update 2FA record
        two_fa, created = TwoFactorAuth.objects.update_or_create(
            user=user,
            phone_number=phone_number,
            defaults={
                'code': code,
                'is_verified': False,
                'expires_at': expires_at
            }
        )
        
        # Send SMS with verification code
        success, msg = send_twilio_sms(phone_number, code)
        
        if not success:
            # Agar SMS fail ho jaye to error raise karein ya handle karein
            raise serializers.ValidationError({"phone_number": f"Failed to send SMS: {msg}"})
        
        return two_fa


class TermsAcceptanceSerializer(serializers.ModelSerializer):
    """Serializer for terms of service acceptance"""
    
    class Meta:
        model = TermsAcceptance
        fields = ['terms_type', 'accepted']
    
    def create(self, validated_data):
        user = self.context['user']
        terms_type = validated_data['terms_type']
        accepted = validated_data['accepted']
        
        # Get request info for audit trail
        request = self.context.get('request')
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create or update terms acceptance
        terms_acceptance, created = TermsAcceptance.objects.update_or_create(
            user=user,
            terms_type=terms_type,
            defaults={
                'accepted': accepted,
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )
        
        return terms_acceptance
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification"""
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    
    def validate(self, attrs):
        email = attrs['email']
        code = attrs['code']
        
        try:
            verification = EmailVerification.objects.get(
                email=email,
                code=code,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
            attrs['verification'] = verification
        except EmailVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification code.")
        
        return attrs


class VerifyTwoFactorSerializer(serializers.Serializer):
    """Serializer for two-factor authentication verification"""
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=4, min_length=4)
    
    def validate(self, attrs):
        phone_number = attrs['phone_number']
        code = attrs['code']
        
        try:
            two_fa = TwoFactorAuth.objects.get(
                phone_number=phone_number,
                code=code,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
            attrs['two_fa'] = two_fa
        except TwoFactorAuth.DoesNotExist:
            raise serializers.ValidationError("Invalid or expired verification code.")
        
        return attrs


class SyndicateProfileSerializer(serializers.ModelSerializer):
    """Serializer for SyndicateProfile model"""
    sectors = SectorSerializer(many=True, read_only=True)
    geographies = GeographySerializer(many=True, read_only=True)
    sector_ids = serializers.PrimaryKeyRelatedField(
        queryset=Sector.objects.all(),
        source='sectors',
        many=True,
        write_only=True,
        required=False
    )
    geography_ids = serializers.PrimaryKeyRelatedField(
        queryset=Geography.objects.all(),
        source='geographies',
        many=True,
        write_only=True,
        required=False
    )
    # Computed full_name field for response
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SyndicateProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at', 'submitted_at']
    
    def get_full_name(self, obj):
        """Dynamically generate full_name from first_name and last_name"""
        first = obj.first_name or ''
        last = obj.last_name or ''
        combined = f"{first} {last}".strip()
        return combined if combined else None
    
    def to_representation(self, instance):
        """Customize the output representation"""
        representation = super().to_representation(instance)
        representation['step1_completed'] = instance.step1_completed
        representation['step2_completed'] = instance.step2_completed
        representation['step3_completed'] = instance.step3_completed
        representation['step4_completed'] = instance.step4_completed
        representation['current_step'] = instance.current_step
        return representation


class SyndicateStep1Serializer(serializers.ModelSerializer):
    """Serializer for Step 1: Lead Info (Personal, Accreditation & Investment Focus)"""
    # full_name is writable for input and computed for output
    full_name = serializers.CharField(required=False, allow_blank=True)
    short_bio = serializers.CharField(required=False, allow_blank=True)
    # Email from the related user object (read-only)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    # Investment Focus fields - sectors and geographies
    sector_ids = serializers.PrimaryKeyRelatedField(
        queryset=Sector.objects.all(),
        source='sectors',
        many=True,
        write_only=True,
        required=False
    )
    sectors = SectorSerializer(many=True, read_only=True)
    
    geography_ids = serializers.PrimaryKeyRelatedField(
        queryset=Geography.objects.all(),
        source='geographies',
        many=True,
        write_only=True,
        required=False
    )
    geographies = GeographySerializer(many=True, read_only=True)
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'email',
            'country_of_residence',
            'current_role_title',
            'years_of_experience',
            'linkedin_profile',
            'typical_check_size',
            'full_name',
            'short_bio',
            'is_accredited',
            'understands_regulatory_requirements',
            'first_name',
            'last_name',
            'bio',
            # Investment Focus fields
            'sectors',
            'sector_ids',
            'geographies',
            'geography_ids',
            'existing_lp_count',
            'lp_base_size',
            'enable_platform_lp_access'
        ]
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
            'bio': {'required': False},
            'existing_lp_count': {'required': False},
            'lp_base_size': {'required': False},
            'enable_platform_lp_access': {'required': False}
        }
    
    def to_representation(self, instance):
        """Override to compute full_name from first_name and last_name for output"""
        data = super().to_representation(instance)
        # Compute full_name from first_name/last_name for output
        first = instance.first_name or ''
        last = instance.last_name or ''
        computed_full_name = f"{first} {last}".strip()
        # Use the stored full_name if it exists, otherwise use computed
        data['full_name'] = instance.full_name or computed_full_name or None
        return data
    
    def validate(self, attrs):
        # Only enforce required fields when not doing a partial update
        if not self.partial and not attrs.get('is_accredited'):
            raise serializers.ValidationError("Accreditation status is required.")

        if not self.partial and not attrs.get('understands_regulatory_requirements'):
            raise serializers.ValidationError("You must acknowledge regulatory requirements.")
        
        return attrs

    def create(self, validated_data):
        # Handle sectors and geographies (M2M fields)
        sectors = validated_data.pop('sectors', None)
        geographies = validated_data.pop('geographies', None)
        
        # Handle full_name -> first_name/last_name during creation
        full_name = validated_data.pop('full_name', None)
        if full_name:
            name_parts = full_name.strip().split(' ', 1)
            validated_data['first_name'] = name_parts[0] if name_parts else ''
            validated_data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
            validated_data['full_name'] = full_name  # Also store the full_name directly

        # Map short_bio to both short_bio and bio fields
        short_bio = validated_data.pop('short_bio', None)
        if short_bio:
            validated_data['short_bio'] = short_bio
            validated_data['bio'] = short_bio

        instance = super().create(validated_data)
        
        # Set M2M relationships after instance creation
        if sectors is not None:
            instance.sectors.set(sectors)
        if geographies is not None:
            instance.geographies.set(geographies)
        
        return instance

    def update(self, instance, validated_data):
        # Handle sectors and geographies (M2M fields)
        sectors = validated_data.pop('sectors', None)
        geographies = validated_data.pop('geographies', None)
        
        # Handle full_name -> first_name/last_name during update
        full_name = validated_data.pop('full_name', None)
        if full_name:
            name_parts = full_name.strip().split(' ', 1)
            instance.first_name = name_parts[0] if name_parts else ''
            instance.last_name = name_parts[1] if len(name_parts) > 1 else ''
            instance.full_name = full_name  # Also store the full_name directly

        # Map short_bio to both short_bio and bio fields
        short_bio = validated_data.pop('short_bio', None)
        if short_bio is not None:
            instance.short_bio = short_bio
            instance.bio = short_bio

        # Update remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        
        # Set M2M relationships
        if sectors is not None:
            instance.sectors.set(sectors)
        if geographies is not None:
            instance.geographies.set(geographies)

        return instance


class SyndicateStep1InvestmentFocusSerializer(serializers.ModelSerializer):
    """Serializer for Step 1: Lead Info (Investment Focus & LP Network)"""
    sector_ids = serializers.PrimaryKeyRelatedField(
        queryset=Sector.objects.all(),
        source='sectors',
        many=True,
        write_only=True,
        required=False
    )
    sectors = SectorSerializer(many=True, read_only=True)
    
    geography_ids = serializers.PrimaryKeyRelatedField(
        queryset=Geography.objects.all(),
        source='geographies',
        many=True,
        write_only=True,
        required=False
    )
    geographies = GeographySerializer(many=True, read_only=True)
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'sectors',
            'sector_ids',
            'geographies',
            'geography_ids',
            'existing_lp_count',
            'lp_base_size',
            'enable_platform_lp_access'
        ]
    
    def validate(self, attrs):
        if not attrs.get('sectors'):
            raise serializers.ValidationError("At least one sector must be selected.")
        
        if not attrs.get('geographies'):
            raise serializers.ValidationError("At least one geography must be selected.")
        
        return attrs


class SyndicateStep2Serializer(serializers.ModelSerializer):
    """Serializer for Step 2: Entity Profile (Syndicate Profile)"""
    
    # Investment Focus fields - sectors and geographies
    sector_ids = serializers.PrimaryKeyRelatedField(
        queryset=Sector.objects.all(),
        source='sectors',
        many=True,
        write_only=True,
        required=False
    )
    sectors = SectorSerializer(many=True, read_only=True)
    
    geography_ids = serializers.PrimaryKeyRelatedField(
        queryset=Geography.objects.all(),
        source='geographies',
        many=True,
        write_only=True,
        required=False
    )
    geographies = GeographySerializer(many=True, read_only=True)
    
    # Team members count (read-only)
    team_members_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'firm_name',
            'description', 
            'logo',
            # Investment focus fields
            'sectors',
            'sector_ids',
            'geographies',
            'geography_ids',
            'existing_lp_count',
            'enable_platform_lp_access',
            # Team members
            'team_members_count'
        ]
        extra_kwargs = {
            'logo': {'required': False},
            'existing_lp_count': {'required': False},
            'enable_platform_lp_access': {'required': False}
        }
    
    def get_team_members_count(self, obj):
        """Return count of team members"""
        return obj.team_members.count() if hasattr(obj, 'team_members') else 0
    
    def validate(self, attrs):
        # Only enforce required fields when not doing a partial update
        if not self.partial:
            if not attrs.get('firm_name'):
                raise serializers.ValidationError({"firm_name": "Firm name is required."})
            
            if not attrs.get('description'):
                raise serializers.ValidationError({"description": "Description is required."})
        
        return attrs
    
    def update(self, instance, validated_data):
        # Handle sectors and geographies (M2M fields)
        sectors = validated_data.pop('sectors', None)
        geographies = validated_data.pop('geographies', None)
        
        # Update remaining fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Set M2M relationships
        if sectors is not None:
            instance.sectors.set(sectors)
        if geographies is not None:
            instance.geographies.set(geographies)
        
        return instance


class SyndicateStep3Serializer(serializers.ModelSerializer):
    """Serializer for Step 3: Compliance & Attestation"""
    # Note: File field is handled separately in the view to avoid pickling issues
    # This serializer handles boolean fields, file field is read-only for response
    
    additional_compliance_policies_url = serializers.SerializerMethodField()
    kyb_verification_status = serializers.SerializerMethodField()
    jurisdiction = serializers.CharField(source='country_of_residence', read_only=True)
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'risk_regulatory_attestation', 'jurisdictional_compliance_acknowledged',
            'additional_compliance_policies', 'additional_compliance_policies_url',
            'kyb_verification_status', 'kyb_verification_completed', 
            'jurisdiction'
        ]
        # Make file field read-only since it's handled separately in the view
        extra_kwargs = {
            'additional_compliance_policies': {'write_only': True, 'required': False},
            'kyb_verification_completed': {'read_only': True}
        }
    
    def get_additional_compliance_policies_url(self, obj):
        if obj.additional_compliance_policies:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.additional_compliance_policies.url)
            return obj.additional_compliance_policies.url
        return None
    
    def get_kyb_verification_status(self, obj):
        """Get KYB verification status with message"""
        if obj.kyb_verification_completed:
            return {
                'status': 'approved',
                'message': 'KYB verification has been approved.'
            }
        return {
            'status': 'pending',
            'message': 'KYB verification is still pending. You can continue, but KYB must be approved before publishing SPVs or accepting LP capital.'
        }
    
    def validate(self, attrs):
        # Only validate attestations on create/update, not on partial updates with no attestation fields
        if not self.partial:
            if not attrs.get('risk_regulatory_attestation'):
                raise serializers.ValidationError({"risk_regulatory_attestation": "Risk & Regulatory Attestation is required."})
            
            # Note: jurisdictional_compliance_acknowledged is optional
        
        return attrs


class SyndicateStep4Serializer(serializers.ModelSerializer):
    """Serializer for Step 4: Final Review & Submit"""
    
    class Meta:
        model = SyndicateProfile
        fields = ['application_submitted']
    
    def validate(self, attrs):
        instance = self.instance
        if not instance.step1_completed:
            raise serializers.ValidationError("Step 1 must be completed before submission.")
        
        if not instance.step2_completed:
            raise serializers.ValidationError("Step 2 must be completed before submission.")
        
        if not instance.step3_completed:
            raise serializers.ValidationError("Step 3 must be completed before submission.")
        
        return attrs
    
    def update(self, instance, validated_data):
        if validated_data.get('application_submitted'):
            instance.application_submitted = True
            instance.submitted_at = timezone.now()
            instance.application_status = 'submitted'
            instance.save()
        return instance


class EntityKYBDetailsSerializer(serializers.ModelSerializer):
    """Serializer for Step 3a: Entity KYB Details - Required Business Info"""
    
    # Read-only URL fields for document uploads
    certificate_of_incorporation_url = serializers.SerializerMethodField()
    registered_address_proof_url = serializers.SerializerMethodField()
    directors_register_url = serializers.SerializerMethodField()
    trust_deed_url = serializers.SerializerMethodField()
    partnership_agreement_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SyndicateProfile
        fields = [
            # Entity Basic Info
            'entity_legal_name',
            'entity_type',
            'country_of_incorporation',
            'registration_number',
            
            # Registered Address
            'registered_street_address',
            'registered_area_landmark',
            'registered_postal_code',
            'registered_city',
            'registered_state',
            'registered_country',
            
            # Operating Address (Optional)
            'operating_street_address',
            'operating_area_landmark',
            'operating_postal_code',
            'operating_city',
            'operating_state',
            'operating_country',
            
            # Company Documents
            'certificate_of_incorporation',
            'certificate_of_incorporation_url',
            'registered_address_proof',
            'registered_address_proof_url',
            'directors_register',
            'directors_register_url',
            
            # Trust/Foundation Documents
            'trust_deed',
            'trust_deed_url',
            
            # Partnership Documents
            'partnership_agreement',
            'partnership_agreement_url',
        ]
        extra_kwargs = {
            'certificate_of_incorporation': {'write_only': True, 'required': False},
            'registered_address_proof': {'write_only': True, 'required': False},
            'directors_register': {'write_only': True, 'required': False},
            'trust_deed': {'write_only': True, 'required': False},
            'partnership_agreement': {'write_only': True, 'required': False},
        }
    
    def get_certificate_of_incorporation_url(self, obj):
        if obj.certificate_of_incorporation:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.certificate_of_incorporation.url)
            return obj.certificate_of_incorporation.url
        return None
    
    def get_registered_address_proof_url(self, obj):
        if obj.registered_address_proof:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.registered_address_proof.url)
            return obj.registered_address_proof.url
        return None
    
    def get_directors_register_url(self, obj):
        if obj.directors_register:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.directors_register.url)
            return obj.directors_register.url
        return None
    
    def get_trust_deed_url(self, obj):
        if obj.trust_deed:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.trust_deed.url)
            return obj.trust_deed.url
        return None
    
    def get_partnership_agreement_url(self, obj):
        if obj.partnership_agreement:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.partnership_agreement.url)
            return obj.partnership_agreement.url
        return None
    
    def validate(self, attrs):
        # Entity legal name is required
        if not self.partial and not attrs.get('entity_legal_name'):
            raise serializers.ValidationError({"entity_legal_name": "Entity legal name is required."})
        
        # Entity type is required
        if not self.partial and not attrs.get('entity_type'):
            raise serializers.ValidationError({"entity_type": "Entity type is required."})
        
        return attrs


# Settings Serializers

class SyndicateSettingsGeneralInfoSerializer(serializers.ModelSerializer):
    """Serializer for Settings: General Information"""
    
    class Meta:
        model = SyndicateProfile
        fields = ['first_name', 'last_name', 'bio', 'link', 'logo']
        extra_kwargs = {
            'logo': {'required': False}
        }


class SyndicateSettingsKYBVerificationSerializer(serializers.ModelSerializer):
    """Serializer for Settings: KYB Verification with all fields"""
    
    # Read-only URL fields for file uploads
    certificate_of_incorporation_url = serializers.SerializerMethodField()
    company_bank_statement_url = serializers.SerializerMethodField()
    company_proof_of_address_url = serializers.SerializerMethodField()
    beneficiary_owner_identity_document_url = serializers.SerializerMethodField()
    beneficiary_owner_proof_of_address_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SyndicateProfile
        fields = [
            # Basic Company Info
            'company_legal_name',
            'kyb_full_name',
            'kyb_position',
            
            # Document Uploads
            'certificate_of_incorporation',
            'certificate_of_incorporation_url',
            'company_bank_statement',
            'company_bank_statement_url',
            
            # Address Information
            'address_line_1',
            'address_line_2',
            'town_city',
            'postal_code',
            'country',
            'company_proof_of_address',
            'company_proof_of_address_url',
            
            # Beneficiary Owner Information
            'beneficiary_owner_identity_document',
            'beneficiary_owner_identity_document_url',
            'beneficiary_owner_proof_of_address',
            'beneficiary_owner_proof_of_address_url',
            
            # S/SE Eligibility
            'sse_eligibility',
            
            # Signing Requirements
            'is_notary_wet_signing',
            'will_require_unlockley',
            
            # Investee Company Contact
            'investee_company_contact_number',
            'investee_company_email',
            
            # Agreement
            'agree_to_investee_terms',
            'kyb_verification_completed',
            'kyb_verification_submitted_at',
        ]
        read_only_fields = ['kyb_verification_submitted_at']
    
    def get_certificate_of_incorporation_url(self, obj):
        if obj.certificate_of_incorporation:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.certificate_of_incorporation.url)
            return obj.certificate_of_incorporation.url
        return None
    
    def get_company_bank_statement_url(self, obj):
        if obj.company_bank_statement:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.company_bank_statement.url)
            return obj.company_bank_statement.url
        return None
    
    def get_company_proof_of_address_url(self, obj):
        if obj.company_proof_of_address:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.company_proof_of_address.url)
            return obj.company_proof_of_address.url
        return None
    
    def get_beneficiary_owner_identity_document_url(self, obj):
        if obj.beneficiary_owner_identity_document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.beneficiary_owner_identity_document.url)
            return obj.beneficiary_owner_identity_document.url
        return None
    
    def get_beneficiary_owner_proof_of_address_url(self, obj):
        if obj.beneficiary_owner_proof_of_address:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.beneficiary_owner_proof_of_address.url)
            return obj.beneficiary_owner_proof_of_address.url
        return None
    
    def validate(self, attrs):
        """Validate KYB data"""
        # If marking as completed, ensure required fields are present
        if attrs.get('kyb_verification_completed'):
            required_fields = [
                'company_legal_name', 'kyb_full_name', 'kyb_position',
                'address_line_1', 'town_city', 'postal_code', 'country',
                'investee_company_email', 'agree_to_investee_terms'
            ]
            
            missing_fields = []
            for field in required_fields:
                # Check in attrs first, then in instance
                value = attrs.get(field) if field in attrs else getattr(self.instance, field, None)
                if not value:
                    missing_fields.append(field)
            
            if missing_fields:
                raise serializers.ValidationError({
                    'error': f"Required fields missing: {', '.join(missing_fields)}"
                })
            
            # Ensure agreement is checked
            agree = attrs.get('agree_to_investee_terms', getattr(self.instance, 'agree_to_investee_terms', False))
            if not agree:
                raise serializers.ValidationError({
                    'agree_to_investee_terms': 'You must agree to investee terms to complete KYB verification'
                })
        
        return attrs
    
    def update(self, instance, validated_data):
        """Update and auto-set submission timestamp if completed"""
        from django.utils import timezone
        
        # If marking as completed, set the timestamp
        if validated_data.get('kyb_verification_completed') and not instance.kyb_verification_completed:
            validated_data['kyb_verification_submitted_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class SyndicateSettingsComplianceSerializer(serializers.ModelSerializer):
    """Serializer for Settings: Compliance & Accreditation documents"""
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'risk_regulatory_attestation',
            'jurisdictional_compliance_acknowledged',
            'additional_compliance_policies'
        ]
        extra_kwargs = {
            'additional_compliance_policies': {'required': False, 'read_only': True}
        }


class SyndicateSettingsJurisdictionalSerializer(serializers.ModelSerializer):
    """Serializer for Settings: Jurisdictional Settings with geography management"""
    geographies = GeographySerializer(many=True, read_only=True)
    geography_ids = serializers.PrimaryKeyRelatedField(
        queryset=Geography.objects.all(),
        write_only=True,
        many=True,
        required=False,
        source='geographies'
    )
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'jurisdictional_compliance_acknowledged',
            'geographies',
            'geography_ids'
        ]
        extra_kwargs = {
            'jurisdictional_compliance_acknowledged': {'required': False}
        }


class SyndicateSettingsPortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Settings: Portfolio Company Outreach with restrict/allow options"""
    
    # For GET requests - show current state
    restrict = serializers.SerializerMethodField(read_only=True)
    allow = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'restrict',
            'allow'
        ]
    
    def get_restrict(self, obj):
        """Return True if platform contact is restricted"""
        return not obj.allow_platform_contact
    
    def get_allow(self, obj):
        """Return True if platform contact is allowed"""
        return obj.allow_platform_contact
    
    def to_internal_value(self, data):
        """Handle both 'restrict' and 'allow' as input fields during PATCH"""
        # Don't call parent since we handle custom logic
        internal_data = {}
        
        if 'restrict' in data:
            # If restrict is sent, set allow_platform_contact to opposite
            internal_data['allow_platform_contact'] = not data['restrict']
        elif 'allow' in data:
            # If allow is sent, set allow_platform_contact directly
            internal_data['allow_platform_contact'] = data['allow']
        
        return internal_data
    
    def update(self, instance, validated_data):
        """Update allow_platform_contact"""
        if 'allow_platform_contact' in validated_data:
            instance.allow_platform_contact = validated_data['allow_platform_contact']
            instance.save()
        return instance


class SyndicateSettingsNotificationsSerializer(serializers.Serializer):
    """Serializer for Settings: Notifications & Communication"""
    email = serializers.EmailField(read_only=True)
    phone_number = serializers.CharField(read_only=True)
    email_verified = serializers.BooleanField(read_only=True)
    phone_verified = serializers.BooleanField(read_only=True)
    two_factor_enabled = serializers.BooleanField(read_only=True)
    two_factor_method = serializers.CharField(read_only=True)
    
    # Notification Preferences
    notification_preference = serializers.CharField(
        write_only=True,
        required=False,
        help_text="Primary notification preference: email, lp_alerts, or deal_updates"
    )
    notify_email_preference = serializers.BooleanField(
        required=False,
        help_text="Receive email notifications"
    )
    notify_new_lp_alerts = serializers.BooleanField(
        required=False,
        help_text="Receive alerts for new LP activities"
    )
    notify_deal_updates = serializers.BooleanField(
        required=False,
        help_text="Receive updates on deal status changes"
    )
    
    def update(self, instance, validated_data):
        """Update notification preferences"""
        if 'notification_preference' in validated_data:
            instance.notification_preference = validated_data['notification_preference']
        if 'notify_email_preference' in validated_data:
            instance.notify_email_preference = validated_data['notify_email_preference']
        if 'notify_new_lp_alerts' in validated_data:
            instance.notify_new_lp_alerts = validated_data['notify_new_lp_alerts']
        if 'notify_deal_updates' in validated_data:
            instance.notify_deal_updates = validated_data['notify_deal_updates']
        instance.save()
        return instance


class FeeRecipientSerializer(serializers.ModelSerializer):
    """Serializer for Fee Recipient settings"""
    id_document_url = serializers.SerializerMethodField()
    proof_of_address_url = serializers.SerializerMethodField()
    recipient_type_display = serializers.CharField(source='get_recipient_type_display', read_only=True)
    
    class Meta:
        model = FeeRecipient
        fields = [
            'id',
            'recipient_type',
            'recipient_type_display',
            'entity_name',
            'residence',
            'tax_id',
            'id_document',
            'id_document_url',
            'proof_of_address',
            'proof_of_address_url',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'id_document_url', 'proof_of_address_url', 'recipient_type_display']
        extra_kwargs = {
            'entity_name': {'required': False},
            'residence': {'required': False},
            'tax_id': {'required': False},
            'id_document': {'required': False},
            'proof_of_address': {'required': False}
        }
    
    def get_id_document_url(self, obj):
        """Get absolute URL for ID document"""
        if obj.id_document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.id_document.url)
            return obj.id_document.url
        return None
    
    def get_proof_of_address_url(self, obj):
        """Get absolute URL for proof of address document"""
        if obj.proof_of_address:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.proof_of_address.url)
            return obj.proof_of_address.url
        return None
    
    def validate(self, data):
        """Validate recipient data based on recipient type"""
        recipient_type = data.get('recipient_type', self.instance.recipient_type if self.instance else 'individual')
        
        if not data.get('entity_name'):
            raise serializers.ValidationError({
                'entity_name': 'Entity name is required for all recipient types'
            })
        
        return data


# Bank Details Serializers

class CreditCardSerializer(serializers.ModelSerializer):
    """Serializer for Credit/Debit Cards"""
    card_type_display = serializers.CharField(source='get_card_type_display', read_only=True)
    card_category_display = serializers.CharField(source='get_card_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = CreditCard
        fields = [
            'id',
            'card_category',
            'card_category_display',
            'card_type',
            'card_type_display',
            'card_number',
            'card_holder_name',
            'expiry_date',
            'cvv',
            'status',
            'status_display',
            'is_primary',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'card_type_display', 'card_category_display', 'status_display']
        extra_kwargs = {
            'card_category': {'required': True},
            'card_type': {'required': True},
            'card_number': {'required': True},
            'card_holder_name': {'required': True},
            'expiry_date': {'required': True}
        }
    
    def validate_card_number(self, value):
        """Validate card number format"""
        # Remove spaces and dashes
        clean_number = value.replace(' ', '').replace('-', '')
        if not clean_number.isdigit() or len(clean_number) < 13 or len(clean_number) > 19:
            raise serializers.ValidationError("Card number must be between 13 and 19 digits")
        return value
    
    def validate_expiry_date(self, value):
        """Validate expiry date format (MM/YY)"""
        if len(value) != 5 or value[2] != '/':
            raise serializers.ValidationError("Expiry date must be in MM/YY format")
        try:
            month, year = value.split('/')
            int(month)
            int(year)
        except ValueError:
            raise serializers.ValidationError("Expiry date must be in MM/YY format")
        return value


class BankAccountSerializer(serializers.ModelSerializer):
    """Serializer for Bank Account"""
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = BankAccount
        fields = [
            'id',
            'bank_name',
            'account_type',
            'account_type_display',
            'account_number',
            'routing_number',
            'swift_code',
            'iban',
            'account_holder_name',
            'status',
            'status_display',
            'is_primary',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'account_type_display', 'status_display']
        extra_kwargs = {
            'bank_name': {'required': True},
            'account_type': {'required': True},
            'account_number': {'required': True},
            'account_holder_name': {'required': True}
        }
    
    def validate(self, data):
        """Validate bank account data"""
        account_type = data.get('account_type')
        
        # IBAN is required for international accounts
        if account_type and not data.get('routing_number') and not data.get('iban'):
            raise serializers.ValidationError({
                'routing_number': 'Either routing number or IBAN must be provided'
            })
        
        return data


class SyndicateSettingsBankDetailsSerializer(serializers.Serializer):
    """Serializer for Bank Details settings"""
    credit_cards = CreditCardSerializer(many=True, read_only=True)
    bank_accounts = BankAccountSerializer(many=True, read_only=True)
    
    def to_representation(self, instance):
        """Custom representation for bank details"""
        return {
            'credit_cards': CreditCardSerializer(
                instance.credit_cards.all(),
                many=True,
                context=self.context
            ).data,
            'bank_accounts': BankAccountSerializer(
                instance.bank_accounts.all(),
                many=True,
                context=self.context
            ).data
        }


# Team Member Serializers

class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember with full details"""
    user_detail = CustomUserSerializer(source='user', read_only=True)
    added_by_detail = CustomUserSerializer(source='added_by', read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamMember
        fields = [
            'id', 'syndicate', 'user', 'user_detail', 'name', 'email',
            'role', 'permissions',
            # Deal Permissions
            'can_create_spvs', 'can_publish_spvs', 'can_upload_deal_materials', 'can_edit_deal_terms',
            # Investor Permissions
            'can_invite_lps', 'can_view_lp_list', 'can_view_lp_commitments', 'can_communicate_with_lps',
            # Operations & Finance
            'can_manage_capital_calls', 'can_update_payment_statuses', 'can_manage_bank_accounts', 'can_send_tax_documents',
            # Compliance
            'can_review_kyc_kyb', 'can_approve_reject_investors', 'can_view_jurisdiction_flags', 'can_access_audit_logs',
            # Team Management
            'can_add_remove_team_members', 'can_edit_roles_permissions',
            # Legacy/General
            'can_access_dashboard', 'can_view_reports',
            # Status
            'invitation_sent', 'invitation_accepted', 'is_active', 'is_registered',
            'added_by', 'added_by_detail', 'added_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_detail', 'added_by_detail', 'is_registered',
            'invitation_sent', 'invitation_accepted', 'added_at', 'updated_at'
        ]
    
    def get_permissions(self, obj):
        """Get permissions as a dictionary"""
        return obj.get_permissions()


class TeamMemberListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for team member list"""
    user_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamMember
        fields = [
            'id', 'name', 'email', 'role', 'user_detail',
            'can_access_dashboard', 'is_active', 'is_registered',
            'added_at'
        ]
    
    def get_user_detail(self, obj):
        """Get user details if registered"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email,
                'first_name': obj.user.first_name,
                'last_name': obj.user.last_name
            }
        return None


class TeamMemberCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating team members"""
    
    class Meta:
        model = TeamMember
        fields = [
            'name', 'email', 'role',
            # Deal Permissions
            'can_create_spvs', 'can_publish_spvs', 'can_upload_deal_materials', 'can_edit_deal_terms',
            # Investor Permissions
            'can_invite_lps', 'can_view_lp_list', 'can_view_lp_commitments', 'can_communicate_with_lps',
            # Operations & Finance
            'can_manage_capital_calls', 'can_update_payment_statuses', 'can_manage_bank_accounts', 'can_send_tax_documents',
            # Compliance
            'can_review_kyc_kyb', 'can_approve_reject_investors', 'can_view_jurisdiction_flags', 'can_access_audit_logs',
            # Team Management
            'can_add_remove_team_members', 'can_edit_roles_permissions',
            # Legacy/General
            'can_access_dashboard', 'can_view_reports'
        ]
    
    def validate_email(self, value):
        """Validate email is not already a team member"""
        syndicate = self.context.get('syndicate')
        if syndicate and TeamMember.objects.filter(syndicate=syndicate, email=value).exists():
            raise serializers.ValidationError("A team member with this email already exists.")
        return value
    
    def create(self, validated_data):
        """Create team member and apply role permissions if enabled"""
        syndicate = self.context.get('syndicate')
        added_by = self.context.get('added_by')
        
        team_member = TeamMember.objects.create(
            syndicate=syndicate,
            added_by=added_by,
            **validated_data
        )
        
        # Apply role-based permissions if enabled
        if syndicate.enable_role_based_access_controls:
            team_member.apply_role_permissions()
            team_member.save()
        
        return team_member


class TeamMemberUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating team member role and permissions"""
    
    class Meta:
        model = TeamMember
        fields = [
            'role',
            # Deal Permissions
            'can_create_spvs', 'can_publish_spvs', 'can_upload_deal_materials', 'can_edit_deal_terms',
            # Investor Permissions
            'can_invite_lps', 'can_view_lp_list', 'can_view_lp_commitments', 'can_communicate_with_lps',
            # Operations & Finance
            'can_manage_capital_calls', 'can_update_payment_statuses', 'can_manage_bank_accounts', 'can_send_tax_documents',
            # Compliance
            'can_review_kyc_kyb', 'can_approve_reject_investors', 'can_view_jurisdiction_flags', 'can_access_audit_logs',
            # Team Management
            'can_add_remove_team_members', 'can_edit_roles_permissions',
            # Legacy/General
            'can_access_dashboard', 'can_view_reports',
            'is_active'
        ]
    
    def update(self, instance, validated_data):
        """Update team member and apply role permissions if role changed"""
        role_changed = 'role' in validated_data and validated_data['role'] != instance.role
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Apply role-based permissions if role changed and RBAC is enabled
        if role_changed and instance.syndicate.enable_role_based_access_controls:
            instance.apply_role_permissions()
        
        instance.save()
        return instance


class TeamMemberRoleUpdateSerializer(serializers.Serializer):
    """Serializer for updating only the role"""
    role = serializers.ChoiceField(choices=TeamMember.ROLE_CHOICES)
    apply_role_permissions = serializers.BooleanField(default=True)


class TeamMemberPermissionsUpdateSerializer(serializers.Serializer):
    """Serializer for updating only permissions"""
    can_access_dashboard = serializers.BooleanField(required=False)
    can_manage_spvs = serializers.BooleanField(required=False)
    can_manage_documents = serializers.BooleanField(required=False)
    can_manage_investors = serializers.BooleanField(required=False)
    can_view_reports = serializers.BooleanField(required=False)
    can_manage_transfers = serializers.BooleanField(required=False)
    can_manage_team = serializers.BooleanField(required=False)
    can_manage_settings = serializers.BooleanField(required=False)


# Compliance Document Serializers

class ComplianceDocumentSerializer(serializers.ModelSerializer):
    """Full serializer for compliance documents"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.get_full_name', read_only=True)
    file_size_mb = serializers.FloatField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ComplianceDocument
        fields = [
            'id', 'syndicate', 'document_name', 'document_type', 'jurisdiction',
            'file', 'file_url', 'original_filename', 'file_size', 'file_size_mb', 'mime_type',
            'status', 'review_notes', 'reviewed_by', 'reviewed_by_name', 'reviewed_at',
            'expiry_date', 'is_expired', 'uploaded_by', 'uploaded_by_name', 'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'uploaded_at', 'updated_at', 'reviewed_by', 'reviewed_at']
    
    def get_file_url(self, obj):
        """Return full URL for file"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class ComplianceDocumentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list view"""
    file_size_mb = serializers.FloatField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    
    class Meta:
        model = ComplianceDocument
        fields = [
            'id', 'document_name', 'document_type', 'document_type_display',
            'jurisdiction', 'status', 'status_display', 'file_size_mb',
            'expiry_date', 'is_expired', 'uploaded_by_name', 'uploaded_at'
        ]


class ComplianceDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for document upload"""
    
    class Meta:
        model = ComplianceDocument
        fields = [
            'document_name', 'document_type', 'jurisdiction', 'file', 'expiry_date'
        ]
    
    def validate_file(self, value):
        """Validate file upload"""
        # Check file size (25MB max)
        max_size = 25 * 1024 * 1024  # 25MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError("File size cannot exceed 25MB")
        
        # Check file type
        allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        'image/jpeg', 'image/png', 'image/jpg']
        allowed_extensions = ['.pdf', '.docx', '.jpg', '.jpeg', '.png']
        
        file_extension = value.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        return value
    
    def create(self, validated_data):
        """Create document with metadata"""
        file = validated_data['file']
        validated_data['original_filename'] = file.name
        validated_data['file_size'] = file.size
        validated_data['mime_type'] = file.content_type
        validated_data['uploaded_by'] = self.context['request'].user
        validated_data['syndicate'] = self.context['syndicate']
        
        return super().create(validated_data)


class ComplianceDocumentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating document status"""
    status = serializers.ChoiceField(choices=ComplianceDocument.STATUS_CHOICES)
    review_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Ensure valid status transition"""
        valid_statuses = ['pending', 'ok', 'exp', 'missing', 'rejected']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value



class QuickProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestorProfile
        fields = ['country_of_residence', 'tax_residency', 'investor_type']
        extra_kwargs = {
            'country_of_residence': {'required': True},
            'tax_residency': {'required': True},
            'investor_type': {'required': True},
        }

    def _load_blocked_countries(self):
        """Load blocked_countries list from accreditation_rules.json; return uppercased codes."""
        try:
            rules_file = os.path.join(settings.BASE_DIR, 'accreditation_rules.json')
            with open(rules_file, 'r', encoding='utf-8') as f:
                all_rules = json.load(f)
            blocked = all_rules.get('blocked_countries', []) or []
            return {c.upper() for c in blocked}
        except Exception:
            return set()

    def _country_name_to_code(self, name):
        """Simple mapping for common blocked country names to ISO codes.
        Add names as needed. Falls back to uppercased input if already a code.
        """
        if not name:
            return None
        mapping = {
            'india': 'IN',
            'china': 'CN',
            'brazil': 'BR',
            'south korea': 'KR',
            'korea, republic of': 'KR',
            'russia': 'RU',
            'iran': 'IR',
            'cuba': 'CU',
            'syria': 'SY',
            'north korea': 'KP',
            'korea, democratic people\'s republic of': 'KP',
            'sudan': 'SD'
        }
        name_norm = name.strip().lower()
        if name_norm in mapping:
            return mapping[name_norm]
        # If user provided 2-letter code already
        if len(name.strip()) == 2:
            return name.strip().upper()
        return None

    def validate_country_of_residence(self, value):
        blocked = self._load_blocked_countries()
        # Try map name to code
        code = self._country_name_to_code(value) or (value.strip().upper() if value else None)
        if code and code in blocked:
            raise serializers.ValidationError("We cannot support investments from your jurisdiction.")
        return value

    def validate_tax_residency(self, value):
        blocked = self._load_blocked_countries()
        code = self._country_name_to_code(value) or (value.strip().upper() if value else None)
        if code and code in blocked:
            raise serializers.ValidationError("Tax residency in a blocked jurisdiction is not supported.")
        return value

    def validate(self, data):
        # Ensure investor_type is present
        it = data.get('investor_type')
        if not it:
            raise serializers.ValidationError({'investor_type': 'This field is required.'})
        return data


# Google OAuth Serializers

class GoogleAuthSerializer(serializers.Serializer):
    """Custom serializer for Google authentication using id_token"""
    id_token = serializers.CharField(required=True, write_only=True)
    access_token = serializers.CharField(required=False, write_only=True)
    code = serializers.CharField(required=False, write_only=True)
    
    def validate_id_token(self, value):
        """Validate and decode id_token"""
        if not value:
            raise serializers.ValidationError("id_token is required")
        return value
    
    def validate(self, attrs):
        """Accept either id_token, access_token, or code"""
        if not attrs.get('id_token') and not attrs.get('access_token') and not attrs.get('code'):
            raise serializers.ValidationError("Either id_token, access_token, or code is required")
        return attrs


class GoogleSignupSerializer(GoogleAuthSerializer):
    """Serializer for Google signup with role requirement"""
    role = serializers.CharField(required=True, write_only=True)
    
    def validate_role(self, value):
        """Validate role is either investor or syndicate"""
        allowed_roles = ['investor', 'syndicate']
        if value not in allowed_roles:
            raise serializers.ValidationError(f"Invalid role. Allowed roles are: {', '.join(allowed_roles)}")
        return value
    
    def validate(self, attrs):
        """Validate that role is provided"""
        attrs = super().validate(attrs)
        if not attrs.get('role'):
            raise serializers.ValidationError("Role is required for signup. Provide 'investor' or 'syndicate'.")
        return attrs


# Beneficial Owner Serializers

class BeneficialOwnerSerializer(serializers.ModelSerializer):
    """Full serializer for BeneficialOwner with all details"""
    identity_document_url = serializers.SerializerMethodField()
    proof_of_address_url = serializers.SerializerMethodField()
    full_address = serializers.ReadOnlyField()
    added_by_detail = serializers.SerializerMethodField()
    
    class Meta:
        model = BeneficialOwner
        fields = [
            'id', 'syndicate',
            # Personal Info
            'full_name', 'date_of_birth', 'nationality', 'email',
            # Address
            'street_address', 'area_landmark', 'postal_code', 
            'city', 'state', 'country', 'full_address',
            # Role & Ownership
            'role', 'ownership_percentage', 'beneficiary_role',
            # KYC Status
            'kyc_status', 'kyc_invite_sent', 'kyc_invite_sent_at', 'kyc_completed_at',
            # Documents
            'identity_document', 'identity_document_url',
            'proof_of_address', 'proof_of_address_url',
            # Metadata
            'is_active', 'added_by', 'added_by_detail', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'identity_document_url', 'proof_of_address_url', 
            'full_address', 'added_by_detail', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'identity_document': {'write_only': True, 'required': False},
            'proof_of_address': {'write_only': True, 'required': False},
        }
    
    def get_identity_document_url(self, obj):
        if obj.identity_document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.identity_document.url)
            return obj.identity_document.url
        return None
    
    def get_proof_of_address_url(self, obj):
        if obj.proof_of_address:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.proof_of_address.url)
            return obj.proof_of_address.url
        return None
    
    def get_added_by_detail(self, obj):
        if obj.added_by:
            return {
                'id': obj.added_by.id,
                'username': obj.added_by.username,
                'email': obj.added_by.email
            }
        return None


class BeneficialOwnerListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing beneficial owners"""
    
    class Meta:
        model = BeneficialOwner
        fields = [
            'id', 'full_name', 'email', 'nationality',
            'role', 'ownership_percentage', 'beneficiary_role',
            'kyc_status', 'is_active', 'created_at'
        ]


class BeneficialOwnerCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating beneficial owners"""
    
    class Meta:
        model = BeneficialOwner
        fields = [
            # Personal Info
            'full_name', 'date_of_birth', 'nationality', 'email',
            # Address
            'street_address', 'area_landmark', 'postal_code', 
            'city', 'state', 'country',
            # Role & Ownership
            'role', 'ownership_percentage', 'beneficiary_role',
        ]
    
    def validate_full_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Full name is required and must be at least 2 characters.")
        return value
    
    def validate_ownership_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Ownership percentage must be between 0 and 100.")
        return value
    
    def create(self, validated_data):
        syndicate = self.context.get('syndicate')
        added_by = self.context.get('added_by')
        
        beneficial_owner = BeneficialOwner.objects.create(
            syndicate=syndicate,
            added_by=added_by,
            **validated_data
        )
        return beneficial_owner


class BeneficialOwnerUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating beneficial owners"""
    
    class Meta:
        model = BeneficialOwner
        fields = [
            # Personal Info
            'full_name', 'date_of_birth', 'nationality', 'email',
            # Address
            'street_address', 'area_landmark', 'postal_code', 
            'city', 'state', 'country',
            # Role & Ownership
            'role', 'ownership_percentage', 'beneficiary_role',
            # KYC Status (admin only)
            'kyc_status',
            # Status
            'is_active'
        ]
    
    def validate_ownership_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Ownership percentage must be between 0 and 100.")
        return value
    

class SyndicateKYBProfileSerializer(serializers.ModelSerializer):
    """Serializer for Syndicate KYB Profile"""
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'kyb_verification_completed',
            'kyb_verification_submitted_at'
        ]
        read_only_fields = [
            'kyb_verification_completed',
            'kyb_verification_submitted_at'
        ]