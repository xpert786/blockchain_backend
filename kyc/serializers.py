from rest_framework import serializers
from .models import KYC
from users.models import CustomUser


class KYCSerializer(serializers.ModelSerializer):
    """Serializer for KYC model"""
    user_details = serializers.SerializerMethodField()
    
    class Meta:
        model = KYC
        fields = '__all__'
        read_only_fields = ['id', 'submitted_at']
    
    def get_user_details(self, obj):
        """Get user details"""
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
        }


class KYCCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating KYC records"""
    
    class Meta:
        model = KYC
        exclude = ['status', 'submitted_at']


class KYCStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating KYC status"""
    
    class Meta:
        model = KYC
        fields = ['status']
    
    def validate_status(self, value):
        """Validate status field"""
        valid_statuses = ['Pending', 'Approved', 'Rejected']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of: {', '.join(valid_statuses)}")
        return value

