from rest_framework import serializers
from .models import SPV, PortfolioCompany, CompanyStage, IncorporationType
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
    
    def validate(self, data):
        """Validate that either portfolio_company or portfolio_company_name is provided"""
        portfolio_company = data.get('portfolio_company')
        portfolio_company_name = data.get('portfolio_company_name', '').strip()
        
        if not portfolio_company and not portfolio_company_name:
            raise serializers.ValidationError({
                'portfolio_company': 'Either select an existing portfolio company or provide a company name.'
            })
        
        return data


class SPVSerializer(serializers.ModelSerializer):
    """Serializer for SPV model with related data"""
    
    created_by = serializers.SerializerMethodField()
    portfolio_company_detail = PortfolioCompanySerializer(source='portfolio_company', read_only=True)
    company_stage_detail = CompanyStageSerializer(source='company_stage', read_only=True)
    incorporation_type_detail = IncorporationTypeSerializer(source='incorporation_type', read_only=True)
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
        """Get creator name"""
        return obj.created_by.get_full_name() or obj.created_by.username

