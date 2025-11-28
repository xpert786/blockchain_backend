from rest_framework import serializers
from .models import CustomUser, Sector, Geography, EmailVerification, TwoFactorAuth, TermsAcceptance, SyndicateProfile, TeamMember, ComplianceDocument
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
        email = validated_data.get('email')
        
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
    # Note: File field is handled separately in the view to avoid pickling issues
    # This serializer handles boolean fields, file field is read-only for response
    
    class Meta:
        model = SyndicateProfile
        fields = [
            'risk_regulatory_attestation', 'jurisdictional_compliance_acknowledged',
            'additional_compliance_policies'
        ]
        # Make file field read-only since it's handled separately in the view
        extra_kwargs = {
            'additional_compliance_policies': {'read_only': True, 'required': False}
        }
    
    def validate(self, attrs):
        if not attrs.get('risk_regulatory_attestation'):
            raise serializers.ValidationError("Risk & Regulatory Attestation is required.")
        
        if not attrs.get('jurisdictional_compliance_acknowledged'):
            raise serializers.ValidationError("Jurisdictional compliance acknowledgment is required.")
        
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
            'can_access_dashboard', 'can_manage_spvs', 'can_manage_documents',
            'can_manage_investors', 'can_view_reports', 'can_manage_transfers',
            'can_manage_team', 'can_manage_settings',
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
            'can_access_dashboard', 'can_manage_spvs', 'can_manage_documents',
            'can_manage_investors', 'can_view_reports', 'can_manage_transfers',
            'can_manage_team', 'can_manage_settings'
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
            'can_access_dashboard', 'can_manage_spvs', 'can_manage_documents',
            'can_manage_investors', 'can_view_reports', 'can_manage_transfers',
            'can_manage_team', 'can_manage_settings',
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

