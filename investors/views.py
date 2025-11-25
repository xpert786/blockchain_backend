from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import InvestorProfile
from .serializers import (
    InvestorProfileSerializer,
    InvestorProfileCreateSerializer,
    InvestorProfileStep1Serializer,
    InvestorProfileStep2Serializer,
    InvestorProfileStep3Serializer,
    InvestorProfileStep4Serializer,
    InvestorProfileStep5Serializer,
    InvestorProfileStep6Serializer,
    InvestorProfileSubmitSerializer
)

# Create your views here.


class InvestorProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing investor profiles.
    
    Provides complete 6-step onboarding process with document uploads.
    """
    serializer_class = InvestorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_queryset(self):
        """Return investor profiles for the current user"""
        user = self.request.user
        
        # Admin can see all profiles
        if user.is_staff or user.is_superuser:
            return InvestorProfile.objects.all()
        
        # Users can only see their own profile
        return InvestorProfile.objects.filter(user=user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return InvestorProfileCreateSerializer
        elif self.action == 'update_step1':
            return InvestorProfileStep1Serializer
        elif self.action == 'update_step2':
            return InvestorProfileStep2Serializer
        elif self.action == 'update_step3':
            return InvestorProfileStep3Serializer
        elif self.action == 'update_step4':
            return InvestorProfileStep4Serializer
        elif self.action == 'update_step5':
            return InvestorProfileStep5Serializer
        elif self.action == 'update_step6' or self.action == 'final_review':
            return InvestorProfileStep6Serializer
        elif self.action == 'submit_application':
            return InvestorProfileSubmitSerializer
        return InvestorProfileSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new investor profile"""
        # Check if user already has a profile
        if hasattr(request.user, 'investor_profile'):
            return Response(
                {'detail': 'Investor profile already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=False, methods=['get'])
    def my_profile(self, request):
        """Get the current user's investor profile"""
        try:
            profile = InvestorProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except InvestorProfile.DoesNotExist:
            return Response(
                {'detail': 'Investor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['get', 'patch'])
    def update_step1(self, request, pk=None):
        """Get or Update Step 1: Basic Information"""
        profile = self.get_object()
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response({
                'step': 1,
                'step_name': 'Basic Information',
                'completed': profile.step1_completed,
                'data': serializer.data
            })
        
        # PATCH method
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full profile with progress
        full_serializer = InvestorProfileSerializer(profile)
        return Response({
            'message': 'Step 1 completed successfully',
            'profile': full_serializer.data
        })
    
    @action(detail=True, methods=['get', 'patch'])
    def update_step2(self, request, pk=None):
        """Get or Update Step 2: KYC / Identity Verification"""
        profile = self.get_object()
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response({
                'step': 2,
                'step_name': 'KYC / Identity Verification',
                'completed': profile.step2_completed,
                'can_access': profile.step1_completed,
                'data': serializer.data
            })
        
        # PATCH method
        # Ensure Step 1 is completed
        if not profile.step1_completed:
            return Response(
                {'detail': 'Please complete Step 1: Basic Information first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full profile with progress
        full_serializer = InvestorProfileSerializer(profile)
        return Response({
            'message': 'Step 2 completed successfully',
            'profile': full_serializer.data
        })
    
    @action(detail=True, methods=['get', 'patch'])
    def update_step3(self, request, pk=None):
        """Get or Update Step 3: Bank Details / Payment Setup"""
        profile = self.get_object()
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response({
                'step': 3,
                'step_name': 'Bank Details / Payment Setup',
                'completed': profile.step3_completed,
                'can_access': profile.step1_completed and profile.step2_completed,
                'data': serializer.data
            })
        
        # PATCH method
        # Ensure previous steps are completed
        if not profile.step1_completed:
            return Response(
                {'detail': 'Please complete Step 1: Basic Information first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not profile.step2_completed:
            return Response(
                {'detail': 'Please complete Step 2: KYC / Identity Verification first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full profile with progress
        full_serializer = InvestorProfileSerializer(profile)
        return Response({
            'message': 'Step 3 completed successfully',
            'profile': full_serializer.data
        })
    
    @action(detail=True, methods=['get', 'patch'])
    def update_step4(self, request, pk=None):
        """Get or Update Step 4: Accreditation (If Applicable)"""
        profile = self.get_object()
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response({
                'step': 4,
                'step_name': 'Accreditation (If Applicable)',
                'completed': profile.step4_completed,
                'can_access': profile.step1_completed and profile.step2_completed and profile.step3_completed,
                'optional': True,
                'data': serializer.data
            })
        
        # PATCH method
        # Ensure previous steps are completed
        if not profile.step1_completed or not profile.step2_completed or not profile.step3_completed:
            return Response(
                {'detail': 'Please complete Steps 1-3 first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full profile with progress
        full_serializer = InvestorProfileSerializer(profile)
        return Response({
            'message': 'Step 4 completed successfully',
            'profile': full_serializer.data
        })
    
    @action(detail=True, methods=['get', 'patch'])
    def update_step5(self, request, pk=None):
        """Get or Update Step 5: Accept Agreements"""
        profile = self.get_object()
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response({
                'step': 5,
                'step_name': 'Accept Agreements',
                'completed': profile.step5_completed,
                'can_access': profile.step1_completed and profile.step2_completed and profile.step3_completed,
                'data': serializer.data
            })
        
        # PATCH method
        # Ensure previous steps are completed
        if not profile.step1_completed or not profile.step2_completed or not profile.step3_completed:
            return Response(
                {'detail': 'Please complete Steps 1-3 first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full profile with progress
        full_serializer = InvestorProfileSerializer(profile)
        return Response({
            'message': 'Step 5 completed successfully',
            'profile': full_serializer.data
        })
    
    @action(detail=True, methods=['get'])
    def final_review(self, request, pk=None):
        """Step 6: Final Review - Display all information for review"""
        profile = self.get_object()
        
        # Ensure all required steps are completed
        if not profile.step1_completed or not profile.step2_completed or not profile.step3_completed or not profile.step5_completed:
            return Response(
                {'detail': 'Please complete all required steps before final review'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = InvestorProfileSerializer(profile)
        return Response({
            'message': 'Review your information before submitting',
            'profile': serializer.data,
            'ready_to_submit': True
        })
    
    @action(detail=True, methods=['post'])
    def submit_application(self, request, pk=None):
        """Submit the investor application"""
        profile = self.get_object()
        
        # Check if already submitted
        if profile.application_submitted:
            return Response(
                {'detail': 'Application already submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(profile, data={'application_submitted': True})
        serializer.is_valid(raise_exception=True)
        serializer.save(
            application_submitted=True,
            submitted_at=timezone.now(),
            application_status='submitted'
        )
        
        # Return full profile
        full_serializer = InvestorProfileSerializer(profile)
        return Response({
            'detail': 'Application submitted successfully',
            'profile': full_serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def choices(self, request):
        """Get all available choices for dropdown fields"""
        return Response({
            'investor_types': InvestorProfile.INVESTOR_TYPE_CHOICES,
            'accreditation_methods': InvestorProfile.ACCREDITATION_METHOD_CHOICES,
            'investment_amounts': InvestorProfile.INVESTMENT_AMOUNT_CHOICES,
            'net_worth_percentages': InvestorProfile.NET_WORTH_PERCENTAGE_CHOICES,
            'investment_strategies': InvestorProfile.INVESTMENT_STRATEGY_CHOICES,
            'venture_experience': InvestorProfile.VENTURE_EXPERIENCE_CHOICES,
            'tech_startup_experience': InvestorProfile.TECH_STARTUP_EXPERIENCE_CHOICES,
            'how_heard': InvestorProfile.HOW_HEARD_CHOICES,
            'reasons': InvestorProfile.REASON_CHOICES,
        })
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get progress information for the profile"""
        profile = self.get_object()
        
        return Response({
            'current_step': profile.current_step,
            'total_steps': 6,
            'steps_completed': {
                'step1_basic_info': profile.step1_completed,
                'step2_kyc': profile.step2_completed,
                'step3_bank_details': profile.step3_completed,
                'step4_accreditation': profile.step4_completed,
                'step5_agreements': profile.step5_completed,
                'step6_submitted': profile.step6_completed,
            },
            'steps_description': {
                'step1': 'Basic Information',
                'step2': 'KYC / Identity Verification',
                'step3': 'Bank Details / Payment Setup',
                'step4': 'Accreditation (If Applicable)',
                'step5': 'Accept Agreements',
                'step6': 'Final Review & Submit',
            },
            'can_submit': all([
                profile.step1_completed,
                profile.step2_completed,
                profile.step3_completed,
                profile.step5_completed
            ]),
            'application_status': profile.application_status,
            'application_submitted': profile.application_submitted,
        })
