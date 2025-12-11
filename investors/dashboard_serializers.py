from rest_framework import serializers
from .dashboard_models import Portfolio, Investment, Notification, KYCStatus, PortfolioPerformance, TaxDocument, TaxSummary, InvestorDocument
from users.models import CustomUser


class InvestmentSerializer(serializers.ModelSerializer):
    """Serializer for Investment model"""
    
    gain_loss = serializers.ReadOnlyField()
    gain_loss_percentage = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    investor_username = serializers.CharField(source='investor.username', read_only=True)
    investor_email = serializers.CharField(source='investor.email', read_only=True)
    
    class Meta:
        model = Investment
        fields = [
            'id',
            'investor',
            'investor_username',
            'investor_email',
            'spv',
            'syndicate_name',
            'sector',
            'stage',
            'investment_type',
            'allocated',
            'raised',
            'target',
            'invested_amount',
            'min_investment',
            'current_value',
            'status',
            'deadline',
            'days_left',
            'track_record',
            'gain_loss',
            'gain_loss_percentage',
            'is_active',
            'created_at',
            'updated_at',
            'invested_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_invested_amount(self, value):
        """Validate invested amount"""
        if value < 0:
            raise serializers.ValidationError("Invested amount cannot be negative")
        return value


class InvestmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new investments"""
    
    class Meta:
        model = Investment
        fields = [
            'syndicate_name',
            'sector',
            'stage',
            'investment_type',
            'allocated',
            'raised',
            'target',
            'invested_amount',
            'min_investment',
            'current_value',
            'deadline',
            'days_left',
        ]
    
    def create(self, validated_data):
        """Create investment with investor from request"""
        validated_data['investor'] = self.context['request'].user
        validated_data['status'] = 'pending'
        return super().create(validated_data)


class PortfolioSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio model"""
    
    portfolio_growth_percentage = serializers.ReadOnlyField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Portfolio
        fields = [
            'id',
            'user',
            'user_username',
            'user_email',
            'total_invested',
            'current_value',
            'unrealized_gain',
            'realized_gain',
            'portfolio_growth_percentage',
            'total_investments_count',
            'active_investments_count',
            'created_at',
            'updated_at',
            'last_calculated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'last_calculated_at']


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer for dashboard overview/summary"""
    
    # KYC Status
    kyc_status = serializers.CharField()
    kyc_verified = serializers.BooleanField()
    
    # Portfolio Summary
    total_investments = serializers.IntegerField()
    portfolio_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_invested = serializers.DecimalField(max_digits=15, decimal_places=2)
    unrealized_gain = serializers.DecimalField(max_digits=15, decimal_places=2)
    portfolio_growth = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Notifications
    total_notifications = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    action_required_notifications = serializers.IntegerField()
    
    # Recent Investments
    recent_investments = InvestmentSerializer(many=True, read_only=True)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    is_unread = serializers.ReadOnlyField()
    is_action_required = serializers.ReadOnlyField()
    user_username = serializers.CharField(source='user.username', read_only=True)
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'user',
            'user_username',
            'notification_type',
            'title',
            'message',
            'status',
            'priority',
            'action_required',
            'action_url',
            'action_label',
            'related_investment',
            'related_spv',
            'icon',
            'metadata',
            'is_unread',
            'is_action_required',
            'time_since_created',
            'created_at',
            'read_at',
            'expires_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'read_at']
    
    def get_time_since_created(self, obj):
        """Get human-readable time since creation"""
        from django.utils import timezone
        from datetime import datetime
        
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 365:
            return f"{diff.days // 365} year(s) ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month(s) ago"
        elif diff.days > 0:
            return f"{diff.days} day(s) ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour(s) ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute(s) ago"
        else:
            return "Just now"


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'notification_type',
            'title',
            'message',
            'priority',
            'action_required',
            'action_url',
            'action_label',
            'related_investment',
            'related_spv',
            'icon',
            'metadata',
        ]
    
    def create(self, validated_data):
        """Create notification with user from request"""
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = 'unread'
        return super().create(validated_data)


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of notification IDs to mark as read. If empty, marks all as read."
    )


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    
    total_notifications = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    action_required_count = serializers.IntegerField()
    
    by_type = serializers.DictField(child=serializers.IntegerField())
    by_priority = serializers.DictField(child=serializers.IntegerField())


class KYCStatusSerializer(serializers.ModelSerializer):
    """Serializer for KYC Status"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = KYCStatus
        fields = [
            'id',
            'user',
            'user_username',
            'status',
            'created_at',
            'updated_at',
            'verified_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class PortfolioPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for Portfolio Performance time-series data"""
    
    class Meta:
        model = PortfolioPerformance
        fields = [
            'id',
            'date',
            'total_invested',
            'current_value',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class PortfolioOverviewSerializer(serializers.Serializer):
    """Serializer for portfolio overview cards data"""
    
    success = serializers.BooleanField(default=True)
    
    # Total Portfolio Value Card
    total_portfolio_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_portfolio_value_formatted = serializers.CharField()
    growth_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    # Total Invested Card
    total_invested = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_invested_formatted = serializers.CharField()
    investments_count = serializers.IntegerField()
    
    # Total Gains Card
    total_gains = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_gains_formatted = serializers.CharField()
    unrealized_gains = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Active Investments Card
    active_investments = serializers.IntegerField()
    pending_investments = serializers.IntegerField()


class InvestmentByRoundSerializer(serializers.Serializer):
    """Serializer for investments aggregated by round/stage"""
    
    round = serializers.CharField()
    stage = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    count = serializers.IntegerField()
    color = serializers.CharField()


class InvestmentBySectorSerializer(serializers.Serializer):
    """Serializer for investments aggregated by sector"""
    
    sector = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    count = serializers.IntegerField()
    percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    color = serializers.CharField()


class InvestorInvestmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for investor's investment with SPV details"""
    
    gain_loss = serializers.ReadOnlyField()
    gain_loss_percentage = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()
    
    # SPV Details
    spv_id = serializers.IntegerField(source='spv.id', read_only=True, allow_null=True)
    spv_display_name = serializers.CharField(source='spv.display_name', read_only=True, allow_null=True)
    spv_company_name = serializers.CharField(source='spv.portfolio_company_name', read_only=True, allow_null=True)
    spv_status = serializers.CharField(source='spv.status', read_only=True, allow_null=True)
    
    # Formatted values
    invested_amount_formatted = serializers.SerializerMethodField()
    current_value_formatted = serializers.SerializerMethodField()
    gain_loss_formatted = serializers.SerializerMethodField()
    updated_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Investment
        fields = [
            'id',
            'syndicate_name',
            'sector',
            'stage',
            'investment_type',
            'invested_amount',
            'invested_amount_formatted',
            'current_value',
            'current_value_formatted',
            'gain_loss',
            'gain_loss_formatted',
            'gain_loss_percentage',
            'status',
            'is_active',
            'spv_id',
            'spv_display_name',
            'spv_company_name',
            'spv_status',
            'updated_ago',
            'created_at',
            'updated_at',
            'invested_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_invested_amount_formatted(self, obj):
        return f"${obj.invested_amount:,.0f}" if obj.invested_amount else "$0"
    
    def get_current_value_formatted(self, obj):
        return f"${obj.current_value:,.0f}" if obj.current_value else "$0"
    
    def get_gain_loss_formatted(self, obj):
        gain = obj.gain_loss
        if gain >= 0:
            return f"${gain:,.0f} (+{obj.gain_loss_percentage}%)"
        return f"-${abs(gain):,.0f} ({obj.gain_loss_percentage}%)"
    
    def get_updated_ago(self, obj):
        """Get human-readable time since last update"""
        from django.utils import timezone
        
        now = timezone.now()
        diff = now - obj.updated_at
        
        if diff.days > 365:
            return f"{diff.days // 365} year(s) ago"
        elif diff.days > 30:
            return f"{diff.days // 30} month(s) ago"
        elif diff.days > 0:
            return f"{diff.days} day(s) ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600} hour(s) ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60} minute(s) ago"
        else:
            return "Just now"


class TaxDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Tax Documents"""
    
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_size_display = serializers.ReadOnlyField()
    investment_name = serializers.CharField(source='investment.syndicate_name', read_only=True, allow_null=True)
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxDocument
        fields = [
            'id',
            'document_type',
            'document_type_display',
            'document_name',
            'tax_year',
            'status',
            'status_display',
            'file',
            'file_size',
            'file_size_display',
            'issue_date',
            'expected_date',
            'investment_name',
            'download_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_download_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class TaxSummarySerializer(serializers.ModelSerializer):
    """Serializer for Tax Summary"""
    
    total_income_formatted = serializers.SerializerMethodField()
    total_deductions_formatted = serializers.SerializerMethodField()
    net_taxable_income_formatted = serializers.SerializerMethodField()
    estimated_tax_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = TaxSummary
        fields = [
            'id',
            'tax_year',
            # Income breakdown
            'dividend_income',
            'capital_gains',
            'interest_income',
            'total_income',
            'total_income_formatted',
            # Deductions breakdown
            'management_fees',
            'professional_services',
            'other_expenses',
            'total_deductions',
            'total_deductions_formatted',
            # Calculated
            'net_taxable_income',
            'net_taxable_income_formatted',
            'estimated_tax',
            'estimated_tax_formatted',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_total_income_formatted(self, obj):
        return f"${obj.total_income:,.0f}" if obj.total_income else "$0"
    
    def get_total_deductions_formatted(self, obj):
        return f"${obj.total_deductions:,.0f}" if obj.total_deductions else "$0"
    
    def get_net_taxable_income_formatted(self, obj):
        return f"${obj.net_taxable_income:,.0f}" if obj.net_taxable_income else "$0"
    
    def get_estimated_tax_formatted(self, obj):
        return f"${obj.estimated_tax:,.0f}" if obj.estimated_tax else "$0"


class TaxOverviewSerializer(serializers.Serializer):
    """Serializer for Tax Center overview cards"""
    
    success = serializers.BooleanField(default=True)
    tax_year = serializers.IntegerField()
    
    # Total Income Card
    total_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_income_formatted = serializers.CharField()
    total_income_label = serializers.CharField()
    
    # Total Deductions Card
    total_deductions = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_deductions_formatted = serializers.CharField()
    total_deductions_label = serializers.CharField()
    
    # Net Taxable Income Card
    net_taxable_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_taxable_income_formatted = serializers.CharField()
    net_taxable_income_label = serializers.CharField()
    
    # Estimated Tax Card
    estimated_tax = serializers.DecimalField(max_digits=15, decimal_places=2)
    estimated_tax_formatted = serializers.CharField()
    estimated_tax_label = serializers.CharField()


class InvestorDocumentSerializer(serializers.ModelSerializer):
    """Serializer for Investor Documents in Document Center"""
    
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_size_display = serializers.ReadOnlyField()
    fund_name_display = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    uploaded_at_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = InvestorDocument
        fields = [
            'id',
            'title',
            'description',
            'category',
            'category_display',
            'file',
            'file_type',
            'file_size',
            'file_size_display',
            'status',
            'status_display',
            'fund_name',
            'fund_name_display',
            'download_url',
            'uploaded_at',
            'uploaded_at_formatted',
            'updated_at',
        ]
        read_only_fields = ['id', 'file_type', 'file_size', 'uploaded_at', 'updated_at']
    
    def get_fund_name_display(self, obj):
        if obj.spv:
            return obj.spv.display_name
        return obj.fund_name or ''
    
    def get_download_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_uploaded_at_formatted(self, obj):
        if obj.uploaded_at:
            return obj.uploaded_at.strftime('%m/%d/%Y')
        return ''


class InvestorDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading investor documents"""
    
    class Meta:
        model = InvestorDocument
        fields = [
            'title',
            'description',
            'category',
            'file',
            'fund_name',
        ]
    
    def create(self, validated_data):
        validated_data['investor'] = self.context['request'].user
        return super().create(validated_data)
