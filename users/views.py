from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser, Syndicate, Sector, Geography, EmailVerification, TwoFactorAuth, TermsAcceptance
from .email_utils import send_verification_email, send_sms_verification, send_2fa_code_email
from .serializers import (
    CustomUserSerializer, 
    UserRegistrationSerializer,
    SyndicateSerializer,
    SyndicateCreateUpdateSerializer,
    SyndicateWithUserCreationSerializer,
    SectorSerializer,
    GeographySerializer,
    RegistrationSerializer,
    EmailVerificationSerializer,
    TwoFactorAuthSerializer,
    TermsAcceptanceSerializer,
    VerifyEmailSerializer,
    VerifyTwoFactorSerializer
)


class CustomUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Allow registration and login without authentication"""
        if self.action in ['register', 'login']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=False, methods=['post', 'options'])
    def register(self, request):
        """
        Register a new user
        POST /api/users/register/
        OPTIONS /api/users/register/ (for CORS preflight)
        """
        # Handle CORS preflight request
        if request.method == 'OPTIONS':
            response = Response({}, status=status.HTTP_200_OK)
            # Add CORS headers
            origin = request.META.get('HTTP_ORIGIN')
            if origin:
                response['Access-Control-Allow-Origin'] = origin
            else:
                response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response
        
        # Handle registration request
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            response = Response({
                'message': 'User registered successfully',
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh)
                }
            }, status=status.HTTP_201_CREATED)
            
            # Add CORS headers to response
            origin = request.META.get('HTTP_ORIGIN')
            if origin:
                response['Access-Control-Allow-Origin'] = origin
            else:
                response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Credentials'] = 'true'
            
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """
        Login user and return JWT tokens
        POST /api/users/login/
        """
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': CustomUserSerializer(user).data
            })
        else:
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)


class SyndicateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing syndicates
    Provides CRUD operations for Syndicate model
    """
    queryset = Syndicate.objects.all()
    serializer_class = SyndicateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Allow syndicate creation without authentication"""
        if self.action == 'create':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def get_serializer_class(self):
        """Use different serializer for create/update"""
        if self.action == 'create':
            # Use special serializer for unauthenticated users
            if not self.request.user.is_authenticated:
                return SyndicateWithUserCreationSerializer
            return SyndicateCreateUpdateSerializer
        elif self.action in ['update', 'partial_update']:
            return SyndicateCreateUpdateSerializer
        return SyndicateSerializer
    
    def get_queryset(self):
        """Filter syndicates based on user role"""
        user = self.request.user
        if user.is_staff or user.role == 'admin':
            # Admins can see all syndicates
            return Syndicate.objects.all().order_by('-time_of_register')
        elif user.role == 'syndicate_manager':
            # Syndicate managers can see their own syndicates
            return Syndicate.objects.filter(manager=user).order_by('-time_of_register')
        else:
            # Investors can see all syndicates (for browsing)
            return Syndicate.objects.all().order_by('-time_of_register')
    
    def perform_create(self, serializer):
        """Set the manager to current user if not provided, or create new user"""
        if not serializer.validated_data.get('manager'):
            if self.request.user.is_authenticated:
                serializer.save(manager=self.request.user)
            else:
                # For unauthenticated users, the serializer handles user creation
                serializer.save()
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'])
    def my_syndicates(self, request):
        """
        Get syndicates managed by current user
        GET /api/syndicates/my_syndicates/
        """
        user = request.user
        syndicates = Syndicate.objects.filter(manager=user)
        serializer = SyndicateSerializer(syndicates, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def newest(self, request):
        """
        Get the newest syndicates
        GET /api/syndicates/newest/
        """
        limit = int(request.query_params.get('limit', 5))
        syndicates = self.get_queryset().order_by('-time_of_register')[:limit]
        serializer = SyndicateSerializer(syndicates, many=True)
        return Response({
            'count': syndicates.count(),
            'limit': limit,
            'results': serializer.data
        })


class SectorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sectors
    """
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Allow read access to all authenticated users, write access to admins only"""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        """Filter sectors by name if search parameter provided"""
        queryset = Sector.objects.all()
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        return queryset.order_by('name')


class GeographyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing geographies
    """
    queryset = Geography.objects.all()
    serializer_class = GeographySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Allow read access to all authenticated users, write access to admins only"""
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        """Filter geographies by region or name if search parameters provided"""
        queryset = Geography.objects.all()
        region = self.request.query_params.get('region', None)
        name = self.request.query_params.get('name', None)
        
        if region:
            queryset = queryset.filter(region__icontains=region)
        if name:
            queryset = queryset.filter(name__icontains=name)
            
        return queryset.order_by('region', 'name')


class SyndicateOnboardingViewSet(viewsets.ViewSet):
    """
    ViewSet for multi-step syndicate onboarding process
    """
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def step1_lead_info(self, request):
        """
        Step 1: Lead Info - Personal and jurisdiction details
        POST /api/onboarding/step1_lead_info/
        """
        data = request.data
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'password2', 'accredited']
        for field in required_fields:
            if field not in data:
                return Response({
                    'error': f'Field "{field}" is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate password match
        if data['password'] != data['password2']:
            return Response({
                'error': 'Passwords do not match'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create user
        try:
            user = CustomUser.objects.create(
                username=data['username'],
                email=data['email'],
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                role='syndicate_manager'
            )
            user.set_password(data['password'])
            user.save()
            
            # Create syndicate with basic info
            syndicate_data = {
                'name': data.get('syndicate_name', f"{user.username}'s Syndicate"),
                'manager': user,
                'accredited': data['accredited'],
                'description': data.get('description', '')
            }
            
            syndicate = Syndicate.objects.create(**syndicate_data)
            
            # Add sectors if provided
            if 'sector_ids' in data:
                sectors = Sector.objects.filter(id__in=data['sector_ids'])
                syndicate.sectors.set(sectors)
            
            # Add geographies if provided
            if 'geography_ids' in data:
                geographies = Geography.objects.filter(id__in=data['geography_ids'])
                syndicate.geographies.set(geographies)
            
            # Update LP network info
            if 'lp_network_count' in data:
                syndicate.lp_network = data['lp_network_count']
            if 'enable_lp_network' in data:
                syndicate.enable_lp_network = data['enable_lp_network']
            
            syndicate.save()
            
            return Response({
                'success': True,
                'message': 'Step 1 completed successfully',
                'user_id': user.id,
                'syndicate_id': syndicate.id,
                'next_step': 'step2_entity_profile'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def step2_entity_profile(self, request):
        """
        Step 2: Entity Profile - Company information and structure
        POST /api/onboarding/step2_entity_profile/
        """
        data = request.data
        
        # Validate required fields
        if 'syndicate_id' not in data:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=data['syndicate_id'])
            
            # Update syndicate with entity profile data
            if 'firm_name' in data:
                syndicate.firm_name = data['firm_name']
            if 'description' in data:
                syndicate.description = data['description']
            if 'team_member' in data:
                syndicate.team_member = data['team_member']
            
            syndicate.save()
            
            return Response({
                'success': True,
                'message': 'Step 2 completed successfully',
                'syndicate_id': syndicate.id,
                'next_step': 'step3_kyb_verification'
            }, status=status.HTTP_200_OK)
            
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def step3_kyb_verification(self, request):
        """
        Step 3: KYB Verification - Business verification and document uploads
        POST /api/onboarding/step3_kyb_verification/
        """
        data = request.data
        
        # Validate required fields
        if 'syndicate_id' not in data:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=data['syndicate_id'])
            
            # Update syndicate with KYB data
            kyb_data = {
                'company_legal_name': data.get('company_legal_name', ''),
                'contact_name': data.get('contact_name', ''),
                'contact_position': data.get('contact_position', ''),
                'address_1': data.get('address_1', ''),
                'address_2': data.get('address_2', ''),
                'city': data.get('city', ''),
                'postal_code': data.get('postal_code', ''),
                'country': data.get('country', ''),
                'contact_number': data.get('contact_number', ''),
                'contact_email': data.get('contact_email', ''),
                'sie_eligibility': data.get('sie_eligibility', ''),
                'notary_required': data.get('notary_required', ''),
                'deed_required': data.get('deed_required', ''),
                'terms_agreed': data.get('terms_agreed', False)
            }
            
            # Store KYB data in additional_compliance_policies for now
            # In a real implementation, you'd create a separate KYB model
            syndicate.additional_compliance_policies = str(kyb_data)
            syndicate.save()
            
            return Response({
                'success': True,
                'message': 'Step 3 completed successfully',
                'syndicate_id': syndicate.id,
                'next_step': 'step4_compliance'
            }, status=status.HTTP_200_OK)
            
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def step4_compliance(self, request):
        """
        Step 4: Compliance & Attestation - Regulatory requirements and attestations
        POST /api/onboarding/step4_compliance/
        """
        data = request.data
        
        # Validate required fields
        if 'syndicate_id' not in data:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=data['syndicate_id'])
            
            # Update compliance information
            if 'risk_regulatory_attestation' in data:
                syndicate.Risk_Regulatory_Attestation = data['risk_regulatory_attestation']
            if 'jurisdictional_requirements' in data:
                syndicate.jurisdictional_requirements = data['jurisdictional_requirements']
            if 'additional_compliance_policies' in data:
                syndicate.additional_compliance_policies = data['additional_compliance_policies']
            
            syndicate.save()
            
            return Response({
                'success': True,
                'message': 'Step 4 completed successfully',
                'syndicate_id': syndicate.id,
                'next_step': 'step5_final_review'
            }, status=status.HTTP_200_OK)
            
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def step5_final_review(self, request):
        """
        Step 5: Final Review & Submit - Final review and submission
        POST /api/onboarding/step5_final_review/
        """
        data = request.data
        
        # Validate required fields
        if 'syndicate_id' not in data:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=data['syndicate_id'])
            
            # Mark syndicate as completed/approved
            # You might want to add a status field to track this
            syndicate.save()
            
            # Generate JWT tokens for the user
            user = syndicate.manager
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'Syndicate onboarding completed successfully!',
                'syndicate': SyndicateSerializer(syndicate).data,
                'user': CustomUserSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
            
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def get_syndicate_progress(self, request):
        """
        Get syndicate onboarding progress
        GET /api/onboarding/get_syndicate_progress/?syndicate_id=1
        """
        syndicate_id = request.query_params.get('syndicate_id')
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id)
            
            # Determine progress based on filled fields
            progress = {
                'step1_completed': bool(syndicate.accredited),
                'step2_completed': bool(syndicate.firm_name),
                'step3_completed': bool(syndicate.additional_compliance_policies),
                'step4_completed': bool(syndicate.Risk_Regulatory_Attestation),
                'step5_completed': True,  # If we can retrieve it, it's completed
                'current_step': 'step1_lead_info'
            }
            
            # Determine current step
            if not progress['step1_completed']:
                progress['current_step'] = 'step1_lead_info'
            elif not progress['step2_completed']:
                progress['current_step'] = 'step2_entity_profile'
            elif not progress['step3_completed']:
                progress['current_step'] = 'step3_kyb_verification'
            elif not progress['step4_completed']:
                progress['current_step'] = 'step4_compliance'
            else:
                progress['current_step'] = 'step5_final_review'
            
            return Response({
                'syndicate_id': syndicate.id,
                'progress': progress,
                'syndicate_data': SyndicateSerializer(syndicate).data
            }, status=status.HTTP_200_OK)
            
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found'
            }, status=status.HTTP_404_NOT_FOUND)


class RegistrationViewSet(viewsets.ViewSet):
    """
    ViewSet for comprehensive user registration with email verification, 2FA, and terms acceptance
    """
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """
        Step 1: Register user with basic information
        POST /api/registration/register/
        """
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'success': True,
                'message': 'User registered successfully. Please verify your email.',
                'user_id': user.id,
                'next_step': 'verify_email'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def send_email_verification(self, request):
        """
        Step 2: Send email verification code
        POST /api/registration/send_email_verification/
        """
        user_id = request.data.get('user_id')
        email = request.data.get('email')
        
        if not user_id or not email:
            return Response({
                'error': 'user_id and email are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = EmailVerificationSerializer(
            data={'email': email, 'code': ''},  # Code will be generated in create method
            context={'user': user}
        )
        
        if serializer.is_valid():
            verification = serializer.save()
            
            return Response({
                'success': True,
                'message': f'Verification code sent to {email}',
                'verification_id': verification.id,
                'next_step': 'verify_email_code'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_email(self, request):
        """
        Step 3: Verify email with 6-digit code
        POST /api/registration/verify_email/
        """
        serializer = VerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            verification = serializer.validated_data['verification']
            user = verification.user
            
            # Mark email as verified
            verification.is_verified = True
            verification.save()
            
            # Update user email verification status
            user.email_verified = True
            user.save()
            
            return Response({
                'success': True,
                'message': 'Email verified successfully',
                'user_id': user.id,
                'next_step': 'send_two_factor'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def send_two_factor(self, request):
        """
        Step 4: Send two-factor authentication code
        POST /api/registration/send_two_factor/
        """
        user_id = request.data.get('user_id')
        phone_number = request.data.get('phone_number')
        
        if not user_id or not phone_number:
            return Response({
                'error': 'user_id and phone_number are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = TwoFactorAuthSerializer(
            data={'phone_number': phone_number, 'code': ''},  # Code will be generated in create method
            context={'user': user}
        )
        
        if serializer.is_valid():
            two_fa = serializer.save()
            
            return Response({
                'success': True,
                'message': f'Two-factor authentication code sent to {phone_number}',
                'two_fa_id': two_fa.id,
                'next_step': 'verify_two_factor'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def verify_two_factor(self, request):
        """
        Step 5: Verify two-factor authentication code
        POST /api/registration/verify_two_factor/
        """
        serializer = VerifyTwoFactorSerializer(data=request.data)
        if serializer.is_valid():
            two_fa = serializer.validated_data['two_fa']
            user = two_fa.user
            
            # Mark 2FA as verified
            two_fa.is_verified = True
            two_fa.save()
            
            # Update user phone verification status
            user.phone_verified = True
            user.phone_number = two_fa.phone_number
            user.save()
            
            return Response({
                'success': True,
                'message': 'Two-factor authentication verified successfully',
                'user_id': user.id,
                'next_step': 'accept_terms'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def accept_terms(self, request):
        """
        Step 6: Accept terms of service
        POST /api/registration/accept_terms/
        """
        user_id = request.data.get('user_id')
        terms_acceptances = request.data.get('terms_acceptances', [])
        
        if not user_id:
            return Response({
                'error': 'user_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Accept all terms
        accepted_terms = []
        for term_data in terms_acceptances:
            serializer = TermsAcceptanceSerializer(
                data=term_data,
                context={'user': user, 'request': request}
            )
            if serializer.is_valid():
                terms_acceptance = serializer.save()
                accepted_terms.append(terms_acceptance)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'message': 'Terms of service accepted successfully',
            'user_id': user.id,
            'accepted_terms': len(accepted_terms),
            'next_step': 'complete_registration'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def complete_registration(self, request):
        """
        Step 7: Complete registration and generate tokens
        POST /api/registration/complete_registration/
        """
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({
                'error': 'user_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if all verifications are complete
        if not user.email_verified:
            return Response({
                'error': 'Email verification required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not user.phone_verified:
            return Response({
                'error': 'Phone verification required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if all required terms are accepted
        required_terms = ['general_terms', 'investing_banking_terms', 'e_sign_consent', 'infrafi_deposit', 'cookie_consent']
        accepted_terms = TermsAcceptance.objects.filter(
            user=user,
            terms_type__in=required_terms,
            accepted=True
        ).values_list('terms_type', flat=True)
        
        missing_terms = set(required_terms) - set(accepted_terms)
        if missing_terms:
            return Response({
                'error': f'Missing terms acceptance: {", ".join(missing_terms)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'success': True,
            'message': 'Registration completed successfully!',
            'user': CustomUserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def get_registration_status(self, request):
        """
        Get registration status for a user
        GET /api/registration/get_registration_status/?user_id=1
        """
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({
                'error': 'user_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check registration progress
        progress = {
            'user_created': True,
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'terms_accepted': False,
            'registration_complete': False
        }
        
        # Check terms acceptance
        required_terms = ['general_terms', 'investing_banking_terms', 'e_sign_consent', 'infrafi_deposit', 'cookie_consent']
        accepted_terms = TermsAcceptance.objects.filter(
            user=user,
            terms_type__in=required_terms,
            accepted=True
        ).values_list('terms_type', flat=True)
        
        progress['terms_accepted'] = len(accepted_terms) == len(required_terms)
        progress['registration_complete'] = (
            progress['email_verified'] and 
            progress['phone_verified'] and 
            progress['terms_accepted']
        )
        
        # Determine current step
        if not progress['email_verified']:
            current_step = 'verify_email'
        elif not progress['phone_verified']:
            current_step = 'verify_two_factor'
        elif not progress['terms_accepted']:
            current_step = 'accept_terms'
        else:
            current_step = 'complete_registration'
        
        return Response({
            'user_id': user.id,
            'progress': progress,
            'current_step': current_step,
            'user_data': CustomUserSerializer(user).data
        }, status=status.HTTP_200_OK)
