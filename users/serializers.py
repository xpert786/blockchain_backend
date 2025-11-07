from rest_framework import serializers
from .models import CustomUser, Sector, Geography, EmailVerification, TwoFactorAuth, TermsAcceptance, SyndicateProfile
from .email_utils import send_verification_email, send_sms_verification
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import random
import string


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
        
        user = CustomUser.objects.create(
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
        email = validated_data['email']
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
    
    class Meta:
        model = TwoFactorAuth
        fields = ['phone_number', 'code']
    
    def create(self, validated_data):
        user = self.context['user']
        phone_number = validated_data['phone_number']
        
        # Generate 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
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
        send_sms_verification(phone_number, code)
        
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
    code = serializers.CharField(max_length=6)
    
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
    
    class Meta:
        model = SyndicateProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at', 'submitted_at']
    
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
    """Serializer for Step 1: Lead Info"""
    sector_ids = serializers.PrimaryKeyRelatedField(
        queryset=Sector.objects.all(),
        source='sectors',
        many=True,
        write_only=True,
        required=True
    )
    geography_ids = serializers.PrimaryKeyRelatedField(
        queryset=Geography.objects.all(),
        source='geographies',
        many=True,
        write_only=True,
        required=True
    )
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'is_accredited', 'understands_regulatory_requirements',
            'sector_ids', 'geography_ids', 'existing_lp_count',
            'enable_platform_lp_access'
        ]
    
    def validate(self, attrs):
        if not attrs.get('is_accredited'):
            raise serializers.ValidationError("Accreditation status is required.")
        
        if not attrs.get('understands_regulatory_requirements'):
            raise serializers.ValidationError("You must acknowledge regulatory requirements.")
        
        if not attrs.get('sectors'):
            raise serializers.ValidationError("At least one sector must be selected.")
        
        if not attrs.get('geographies'):
            raise serializers.ValidationError("At least one geography must be selected.")
        
        return attrs


class SyndicateStep2Serializer(serializers.ModelSerializer):
    """Serializer for Step 2: Entity Profile"""
    
    class Meta:
        model = SyndicateProfile
        fields = ['firm_name', 'description', 'logo']
    
    def validate(self, attrs):
        if not attrs.get('firm_name'):
            raise serializers.ValidationError("Firm name is required.")
        
        if not attrs.get('description'):
            raise serializers.ValidationError("Description is required.")
        
        return attrs


class SyndicateStep3Serializer(serializers.ModelSerializer):
    """Serializer for Step 3: Compliance & Attestation"""
    additional_compliance_policies = serializers.FileField(required=False, allow_null=True)
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'risk_regulatory_attestation', 'jurisdictional_compliance_acknowledged',
            'additional_compliance_policies'
        ]
    
    def validate(self, attrs):
        if not attrs.get('risk_regulatory_attestation'):
            raise serializers.ValidationError("Risk & Regulatory Attestation is required.")
        
        if not attrs.get('jurisdictional_compliance_acknowledged'):
            raise serializers.ValidationError("Jurisdictional compliance acknowledgment is required.")
        
        return attrs
    
    def to_internal_value(self, data):
        """Override to handle file fields properly"""
        request = self.context.get('request')
        
        # Handle file field - if it's in FILES, use it; if it's in data as empty/null, remove it
        if isinstance(data, dict):
            data = data.copy()
            if 'additional_compliance_policies' in data:
                # If request has FILES and field is not there, it might be empty/null
                if request and hasattr(request, 'FILES'):
                    if 'additional_compliance_policies' not in request.FILES:
                        value = data.get('additional_compliance_policies')
                        if value == '' or value is None or value == 'null':
                            data.pop('additional_compliance_policies', None)
                else:
                    # No FILES (JSON request) - if value is empty/null, remove it
                    value = data.get('additional_compliance_policies')
                    if value == '' or value is None or value == 'null':
                        data.pop('additional_compliance_policies', None)
        
        return super().to_internal_value(data)


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

