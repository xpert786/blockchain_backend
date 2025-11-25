from rest_framework import serializers
from .dashboard_models import Portfolio, Investment, Notification, KYCStatus
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
