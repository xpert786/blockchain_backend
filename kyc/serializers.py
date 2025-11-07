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
    # Explicitly define all file fields as optional
    certificate_of_incorporation = serializers.FileField(required=False, allow_null=True)
    company_bank_statement = serializers.FileField(required=False, allow_null=True)
    company_proof_of_address = serializers.FileField(required=False, allow_null=True)
    owner_identity_doc = serializers.FileField(required=False, allow_null=True)
    owner_proof_of_address = serializers.FileField(required=False, allow_null=True)
    
    class Meta:
        model = KYC
        exclude = ['status', 'submitted_at']
    
    def to_internal_value(self, data):
        """Override to handle file fields properly - filter out non-file values"""
        # Get request from context to access FILES
        request = self.context.get('request')
        
        # All file fields in the model
        file_fields = [
            'certificate_of_incorporation',
            'company_bank_statement',
            'company_proof_of_address',
            'owner_identity_doc',
            'owner_proof_of_address'
        ]
        
        # Handle QueryDict (from multipart/form-data) or regular dict
        from django.http import QueryDict
        
        if isinstance(data, QueryDict):
            # QueryDict - check if field is in data but not in FILES
            if request and hasattr(request, 'FILES'):
                for field in file_fields:
                    if field in data and field not in request.FILES:
                        value = data.get(field)
                        if value == '' or value is None or value == 'null':
                            # Create new QueryDict without this field
                            data = data.copy()
                            data.pop(field, None)
                            break
        elif isinstance(data, dict):
            # Regular dict (from JSONParser) - we can modify directly
            data = data.copy()
            for field in file_fields:
                if field in data:
                    value = data.get(field)
                    # If request has FILES and field is not there, or if value is empty/null, remove it
                    if request and hasattr(request, 'FILES'):
                        if field not in request.FILES and (value == '' or value is None or value == 'null'):
                            data.pop(field, None)
                    elif value == '' or value is None or value == 'null':
                        # No FILES (JSON request) and value is empty/null - remove it
                        data.pop(field, None)
        
        return super().to_internal_value(data)


class KYCUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating KYC records (supports file uploads)"""
    # Explicitly define all file fields as optional
    certificate_of_incorporation = serializers.FileField(required=False, allow_null=True)
    company_bank_statement = serializers.FileField(required=False, allow_null=True)
    company_proof_of_address = serializers.FileField(required=False, allow_null=True)
    owner_identity_doc = serializers.FileField(required=False, allow_null=True)
    owner_proof_of_address = serializers.FileField(required=False, allow_null=True)
    
    class Meta:
        model = KYC
        exclude = ['user', 'status', 'submitted_at']
    
    def to_internal_value(self, data):
        """Override to handle file fields properly - filter out non-file values"""
        # Get request from context to access FILES
        request = self.context.get('request')
        
        # All file fields in the model
        file_fields = [
            'certificate_of_incorporation',
            'company_bank_statement',
            'company_proof_of_address',
            'owner_identity_doc',
            'owner_proof_of_address'
        ]
        
        # Handle QueryDict (from multipart/form-data) or regular dict
        from django.http import QueryDict
        
        if isinstance(data, QueryDict):
            # QueryDict - check if field is in data but not in FILES
            if request and hasattr(request, 'FILES'):
                for field in file_fields:
                    if field in data and field not in request.FILES:
                        value = data.get(field)
                        if value == '' or value is None or value == 'null':
                            # Create new QueryDict without this field
                            data = data.copy()
                            data.pop(field, None)
                            break
        elif isinstance(data, dict):
            # Regular dict (from JSONParser) - we can modify directly
            data = data.copy()
            for field in file_fields:
                if field in data:
                    value = data.get(field)
                    # If request has FILES and field is not there, or if value is empty/null, remove it
                    if request and hasattr(request, 'FILES'):
                        if field not in request.FILES and (value == '' or value is None or value == 'null'):
                            data.pop(field, None)
                    elif value == '' or value is None or value == 'null':
                        # No FILES (JSON request) and value is empty/null - remove it
                        data.pop(field, None)
        
        return super().to_internal_value(data)


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

