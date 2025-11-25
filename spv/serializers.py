from django.db.models import Max
from rest_framework import serializers
from .models import (
    SPV, PortfolioCompany, CompanyStage, IncorporationType,
    InstrumentType, ShareClass, Round, MasterPartnershipEntity
)
from users.models import CustomUser


class CompanyStageSerializer(serializers.ModelSerializer):
    """Serializer for CompanyStage model"""
    
    class Meta:
        model = CompanyStage
        fields = ['id', 'name', 'description', 'order']
        read_only_fields = ['id']


class IncorporationTypeSerializer(serializers.ModelSerializer):
    """Serializer for IncorporationType model"""
    
    class Meta:
        model = IncorporationType
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']


class InstrumentTypeSerializer(serializers.ModelSerializer):
    """Serializer for InstrumentType model"""
    
    class Meta:
        model = InstrumentType
        fields = ['id', 'name', 'description', 'order']
        read_only_fields = ['id']


class ShareClassSerializer(serializers.ModelSerializer):
    """Serializer for ShareClass model"""
    
    class Meta:
        model = ShareClass
        fields = ['id', 'name', 'description', 'order']
        read_only_fields = ['id']


class RoundSerializer(serializers.ModelSerializer):
    """Serializer for Round model"""
    
    class Meta:
        model = Round
        fields = ['id', 'name', 'description', 'order']
        read_only_fields = ['id']


class MasterPartnershipEntitySerializer(serializers.ModelSerializer):
    """Serializer for MasterPartnershipEntity model"""
    
    class Meta:
        model = MasterPartnershipEntity
        fields = ['id', 'name', 'description', 'order']
        read_only_fields = ['id']


class PortfolioCompanySerializer(serializers.ModelSerializer):
    """Serializer for PortfolioCompany model"""
    
    class Meta:
        model = PortfolioCompany
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']


class SPVCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating SPV deals"""
    
    portfolio_company_name = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text="Portfolio company name (if not selecting from existing)"
    )
    lp_invite_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True,
        default=list
    )
    invite_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )
    deal_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )
    company_stage_name = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )
    incorporation_type_name = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )
    instrument_type_name = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )
    share_class_name = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )
    round_name = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )
    master_partnership_entity_name = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True
    )
    
    class Meta:
        model = SPV
        fields = [
            'display_name',
            'portfolio_company',
            'portfolio_company_name',
            'company_stage',
            'country_of_incorporation',
            'incorporation_type',
            'founder_email',
            'pitch_deck',
            # Step 2: Terms fields
            'transaction_type',
            'instrument_type',
            'valuation_type',
            'share_class',
            'round',
            'company_stage_name',
            'incorporation_type_name',
            'instrument_type_name',
            'share_class_name',
            'round_name',
            'round_size',
            'allocation',
            # Step 3: Adviser & Legal Structure fields
            'adviser_entity',
            'master_partnership_entity',
            'master_partnership_entity_name',
            'fund_lead',
            # Step 4: Fundraising & Jurisdiction
            'jurisdiction',
            'entity_type',
            'minimum_lp_investment',
            'target_closing_date',
            'total_carry_percentage',
            'carry_recipient',
            'gp_commitment',
            'deal_partners',
            'deal_name',
            'access_mode',
            # Step 5: Invite LPs & Additional Information
            'lp_invite_emails',
            'lp_invite_message',
            'lead_carry_percentage',
            'investment_visibility',
            'auto_invite_active_spvs',
            'invite_private_note',
            'invite_tags',
            'deal_tags',
            'syndicate_selection',
            'deal_memo',
            'supporting_document',
        ]
    
    def validate(self, data):
        """Validate that either portfolio_company or portfolio_company_name is provided"""
        portfolio_company = data.get('portfolio_company')
        portfolio_company_name = data.get('portfolio_company_name', '').strip()
        
        if not portfolio_company and not portfolio_company_name:
            raise serializers.ValidationError({
                'portfolio_company': 'Either select an existing portfolio company or provide a company name.'
            })
        
        return data

    def _get_next_order(self, model):
        """Return the next order value for ordered lookup models."""
        max_order = model.objects.aggregate(max_order=Max('order'))['max_order']
        return (max_order or 0) + 1

    def _ensure_lookup(self, validated_data, field_name, name_value, model, has_order=False):
        """
        Ensure a lookup relation exists by ID or create by name.
        """
        if validated_data.get(field_name) or not name_value:
            return

        defaults = {'description': ''}
        if has_order and hasattr(model, 'order'):
            defaults['order'] = self._get_next_order(model)

        lookup_obj, _ = model.objects.get_or_create(
            name=name_value,
            defaults=defaults
        )
        validated_data[field_name] = lookup_obj

    def create(self, validated_data):
        company_stage_name = validated_data.pop('company_stage_name', '').strip()
        incorporation_type_name = validated_data.pop('incorporation_type_name', '').strip()
        instrument_type_name = validated_data.pop('instrument_type_name', '').strip()
        share_class_name = validated_data.pop('share_class_name', '').strip()
        round_name = validated_data.pop('round_name', '').strip()
        master_partnership_entity_name = validated_data.pop('master_partnership_entity_name', '').strip()

        self._ensure_lookup(
            validated_data,
            'company_stage',
            company_stage_name,
            CompanyStage,
            has_order=True
        )
        self._ensure_lookup(
            validated_data,
            'incorporation_type',
            incorporation_type_name,
            IncorporationType,
            has_order=False
        )
        self._ensure_lookup(
            validated_data,
            'instrument_type',
            instrument_type_name,
            InstrumentType,
            has_order=True
        )
        self._ensure_lookup(
            validated_data,
            'share_class',
            share_class_name,
            ShareClass,
            has_order=True
        )
        self._ensure_lookup(
            validated_data,
            'round',
            round_name,
            Round,
            has_order=True
        )
        self._ensure_lookup(
            validated_data,
            'master_partnership_entity',
            master_partnership_entity_name,
            MasterPartnershipEntity,
            has_order=True
        )

        portfolio_company = validated_data.get('portfolio_company')
        portfolio_company_name = validated_data.get('portfolio_company_name', '').strip()

        if not portfolio_company and portfolio_company_name:
            portfolio_company, _ = PortfolioCompany.objects.get_or_create(
                name=portfolio_company_name,
                defaults={'description': ''}
            )
            validated_data['portfolio_company'] = portfolio_company

        if validated_data.get('portfolio_company'):
            validated_data['portfolio_company_name'] = (
                validated_data.get('portfolio_company_name')
                or validated_data['portfolio_company'].name
            )

        return super().create(validated_data)


class SPVSerializer(serializers.ModelSerializer):
    """Serializer for SPV model with related data"""
    
    created_by = serializers.SerializerMethodField()
    portfolio_company_detail = PortfolioCompanySerializer(source='portfolio_company', read_only=True)
    company_stage_detail = CompanyStageSerializer(source='company_stage', read_only=True)
    incorporation_type_detail = IncorporationTypeSerializer(source='incorporation_type', read_only=True)
    instrument_type_detail = InstrumentTypeSerializer(source='instrument_type', read_only=True)
    share_class_detail = ShareClassSerializer(source='share_class', read_only=True)
    round_detail = RoundSerializer(source='round', read_only=True)
    master_partnership_entity_detail = MasterPartnershipEntitySerializer(source='master_partnership_entity', read_only=True)
    fund_lead_detail = serializers.SerializerMethodField()
    company_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = SPV
        fields = [
            'id',
            'created_by',
            'display_name',
            'portfolio_company',
            'portfolio_company_name',
            'portfolio_company_detail',
            'company_name',
            'company_stage',
            'company_stage_detail',
            'country_of_incorporation',
            'incorporation_type',
            'incorporation_type_detail',
            'founder_email',
            'pitch_deck',
            # Step 2: Terms fields
            'transaction_type',
            'instrument_type',
            'instrument_type_detail',
            'valuation_type',
            'share_class',
            'share_class_detail',
            'round',
            'round_detail',
            'round_size',
            'allocation',
            # Step 3: Adviser & Legal Structure fields
            'adviser_entity',
            'master_partnership_entity',
            'master_partnership_entity_detail',
            'fund_lead',
            'fund_lead_detail',
            # Step 4: Fundraising & Jurisdiction
            'jurisdiction',
            'entity_type',
            'minimum_lp_investment',
            'target_closing_date',
            'total_carry_percentage',
            'carry_recipient',
            'gp_commitment',
            'deal_partners',
            'deal_name',
            'access_mode',
            # Step 5: Invite LPs & Additional Information
            'lp_invite_emails',
            'lp_invite_message',
            'lead_carry_percentage',
            'investment_visibility',
            'auto_invite_active_spvs',
            'invite_private_note',
            'invite_tags',
            'deal_tags',
            'syndicate_selection',
            'deal_memo',
            'supporting_document',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'status', 'created_at', 'updated_at']
    
    def get_created_by(self, obj):
        """Get creator user details"""
        return {
            'id': obj.created_by.id,
            'username': obj.created_by.username,
            'email': obj.created_by.email,
            'full_name': obj.created_by.get_full_name() or obj.created_by.username,
        }
    
    def get_fund_lead_detail(self, obj):
        """Get fund lead user details"""
        if obj.fund_lead:
            return {
                'id': obj.fund_lead.id,
                'username': obj.fund_lead.username,
                'email': obj.fund_lead.email,
                'full_name': obj.fund_lead.get_full_name() or obj.fund_lead.username,
            }
        return None


class SPVListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for SPV list views"""
    
    company_name = serializers.CharField(read_only=True)
    company_stage_name = serializers.CharField(source='company_stage.name', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SPV
        fields = [
            'id',
            'display_name',
            'company_name',
            'company_stage_name',
            'founder_email',
            'status',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_created_by_name(self, obj):
        """Get creator's full name or username"""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username or obj.created_by.email
        return None
    
class SPVStep1CreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPV
        fields = [
            'display_name',
            'portfolio_company',
            'portfolio_company_name',
            'company_stage',
            'country_of_incorporation',
            'incorporation_type',
            'founder_email',
            'pitch_deck'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        return SPV.objects.create(created_by=request.user, **validated_data)


class SPVStep1Serializer(serializers.ModelSerializer):
    """Serializer for updating SPV Step 1 (Basic Information) fields only"""
    
    class Meta:
        model = SPV
        fields = [
            'display_name',
            'portfolio_company',
            'portfolio_company_name',
            'company_stage',
            'country_of_incorporation',
            'incorporation_type',
            'founder_email',
            'pitch_deck',
        ]


class SPVStep2Serializer(serializers.ModelSerializer):
    """Serializer for updating SPV Step 2 (Terms) fields only"""
    
    class Meta:
        model = SPV
        fields = [
            'transaction_type',
            'instrument_type',
            'valuation_type',
            'share_class',
            'round',
            'round_size',
            'allocation',
        ]


class SPVStep3Serializer(serializers.ModelSerializer):
    """Serializer for updating SPV Step 3 (Adviser & Legal Structure) fields only"""
    
    class Meta:
        model = SPV
        fields = [
            'adviser_entity',
            'master_partnership_entity',
            'fund_lead',
        ]


class SPVStep4Serializer(serializers.ModelSerializer):
    """Serializer for updating SPV Step 4 (Fundraising & Jurisdiction) fields"""
    
    target_closing_date = serializers.DateField(required=False, allow_null=True)
    
    class Meta:
        model = SPV
        fields = [
            'jurisdiction',
            'entity_type',
            'minimum_lp_investment',
            'target_closing_date',
            'total_carry_percentage',
            'carry_recipient',
            'gp_commitment',
            'deal_partners',
            'deal_name',
            'access_mode',
        ]


class SPVStep5Serializer(serializers.ModelSerializer):
    """Serializer for updating SPV Step 5 (Invite LPs & Additional Info) fields"""
    
    lp_invite_emails = serializers.ListField(
        child=serializers.EmailField(),
        required=False,
        allow_empty=True,
        default=list
    )
    invite_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )
    deal_tags = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )
    
    class Meta:
        model = SPV
        fields = [
            'lp_invite_emails',
            'lp_invite_message',
            'lead_carry_percentage',
            'investment_visibility',
            'auto_invite_active_spvs',
            'invite_private_note',
            'invite_tags',
            'deal_tags',
            'syndicate_selection',
            'deal_memo',
            'supporting_document',
            'access_mode',
        ]


class SPVStep6Serializer(serializers.ModelSerializer):
    """Serializer for updating SPV Step 6 (Additional Information) fields"""
    
    class Meta:
        model = SPV
        fields = [
            'deal_name',
            'syndicate_selection',
            'supporting_document',

            # Final Submission Legal Confirmations
            'legal_review_confirmed',
            'terms_accepted',
            'electronic_signature_confirmed',
        ]
    def validate(self, attrs):

        # Only validate if user is submitting final step
        # (optional: but recommended)
        if self.context.get("final_submit", False):

            if not attrs.get("legal_review_confirmed"):
                raise serializers.ValidationError("You must confirm the legal review.")

            if not attrs.get("terms_accepted"):
                raise serializers.ValidationError("You must accept the terms and conditions.")

            if not attrs.get("electronic_signature_confirmed"):
                raise serializers.ValidationError("You must provide electronic signature.")

        return attrs

