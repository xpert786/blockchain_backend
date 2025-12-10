import json
import os
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import InvestorProfile
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    InvestorProfileSerializer,
    InvestorProfileCreateSerializer,
    InvestorProfileStep1Serializer,
    InvestorProfileStep2Serializer,
    InvestorProfileStep3Serializer,
    InvestorProfileAccreditationCheckSerializer,
    InvestorProfileStep4Serializer,
    InvestorProfileStep5Serializer,
    InvestorProfileStep6Serializer,
    InvestorProfileSubmitSerializer,
    InvestorOnboardingProgressSerializer
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
        elif self.action == 'accreditation_check':
            return InvestorProfileAccreditationCheckSerializer
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
    
    def update(self, request, *args, **kwargs):
        """Update investor profile"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Profile updated successfully',
            'profile': serializer.data
        })
    
    def partial_update(self, request, *args, **kwargs):
        """Partially update investor profile"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)
    
    @action(detail=False, methods=['get', 'patch'])
    def my_profile(self, request):
        """Get or Update the current user's investor profile"""
        try:
            profile = InvestorProfile.objects.get(user=request.user)
        except InvestorProfile.DoesNotExist:
            return Response(
                {'detail': 'Investor profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        
        # PATCH method
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'profile': serializer.data
        })
    
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
        # If client is trying to update country_of_residence, check blocked list
        if request.method == 'PATCH':
            new_country = request.data.get('country_of_residence')
            if new_country:
                try:
                    rules_file = os.path.join(settings.BASE_DIR, 'accreditation_rules.json')
                    with open(rules_file, 'r', encoding='utf-8') as f:
                        all_rules = json.load(f)
                    blocked = all_rules.get('blocked_countries', []) or []
                except Exception:
                    blocked = []

                # Normalize to 2-letter code uppercase if provided as such
                code = (new_country or '').strip()
                code_upper = code.upper()
                # Accept either two-letter code or full country name 'India' -> 'IN' not covered here
                if code_upper in blocked or code_upper[:2] in blocked:
                    return Response({'detail': f"Investors from '{new_country}' are blocked and cannot set this country."}, status=status.HTTP_400_BAD_REQUEST)

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
    def accreditation_check(self, request, pk=None):
        """Get or Update Jurisdiction-Aware Accreditation Check (New Screen before Step 4)"""
        profile = self.get_object()
        
        if request.method == 'GET':
            # Get accreditation rules based on user's country
            country = profile.country_of_residence or 'US'
            jurisdiction_code = self._get_jurisdiction_code(country)
            
            # Load accreditation rules
            rules_data = self._load_accreditation_rules(jurisdiction_code)
            
            serializer = InvestorProfileAccreditationCheckSerializer(profile)
            return Response({
                'step': 'accreditation_check',
                'step_name': 'Jurisdiction-Aware Accreditation Check',
                'completed': profile.accreditation_check_completed,
                'can_access': profile.step1_completed and profile.step2_completed and profile.step3_completed,
                'jurisdiction': jurisdiction_code,
                'country': country,
                'rules': rules_data,
                'data': serializer.data
            })
        
        # PATCH method
        # NOTE: allow short-profile updates here (do not require Steps 1-3 to be completed)

        # If client is trying to set a jurisdiction that is blocked, reject early
        submitted_j = request.data.get('accreditation_jurisdiction')
        try:
            rules_file = os.path.join(settings.BASE_DIR, 'accreditation_rules.json')
            with open(rules_file, 'r', encoding='utf-8') as f:
                all_rules = json.load(f)
            blocked = all_rules.get('blocked_countries', []) or []
        except Exception:
            blocked = []

        if submitted_j:
            # Normalize possible inputs: two-letter codes or lowercase keys
            maybe_code = submitted_j.strip().upper()
            # If client passed a lowercase key like 'in' or 'india', handle simple cases
            if maybe_code in blocked or maybe_code[:2] in blocked:
                return Response({'detail': f"Investors from jurisdiction '{submitted_j}' are blocked and cannot complete accreditation."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = InvestorProfileAccreditationCheckSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Set completion timestamp if completing the check
        if request.data.get('accreditation_check_completed') and not profile.accreditation_check_completed:
            serializer.save(accreditation_check_completed_at=timezone.now())
        else:
            serializer.save()
        
        # Return full profile with progress
        full_serializer = InvestorProfileSerializer(profile)
        return Response({
            'message': 'Accreditation check completed successfully',
            'profile': full_serializer.data
        })
    
    def _get_jurisdiction_code(self, country):
        """Map country name to jurisdiction code"""
        country_mapping = {
            'United States': 'us',
            'US': 'us',
            'USA': 'us',
            'Singapore': 'sg',
            'SG': 'sg',
            'United Kingdom': 'uk',
            'UK': 'uk',
            'GB': 'uk',
            'Canada': 'default',
            'CA': 'default',
            'United Arab Emirates': 'uae',
            'UAE': 'uae',
            'Australia': 'au',
            'AU': 'au',
            'Hong Kong': 'hk',
            'HK': 'hk',
            'European Union': 'eu',
            'EU': 'eu',
        }
        # Return the JSON-friendly lowercase jurisdiction key; default to 'default'
        return country_mapping.get(country, 'default')
    
    def _load_accreditation_rules(self, jurisdiction_code):
        """Load accreditation rules from JSON file"""
        try:
            # Get the path to accreditation_rules.json
            base_dir = settings.BASE_DIR
            rules_file_path = os.path.join(base_dir, 'accreditation_rules.json')
            
            with open(rules_file_path, 'r', encoding='utf-8') as f:
                all_rules = json.load(f)

            # Normalize key
            key = (jurisdiction_code or '').lower()

            # If exact key exists, return it; otherwise fall back to 'default'
            if key in all_rules:
                return all_rules.get(key)
            if 'default' in all_rules:
                return all_rules.get('default')

            # As an extra fallback, try 'us' then any top-level entry
            return all_rules.get('us') or next(iter(all_rules.values()), {})
        except FileNotFoundError:
            # Return default US rules if file not found
            return {
                "jurisdiction": "United States",
                "regulation": "Reg D Rule 501(a)",
                "rules": [
                    {
                        "id": "income_200k_2_years",
                        "text": "My income exceeded $200,000 ($300,000 joint) for the last two years",
                        "required": False
                    },
                    {
                        "id": "net_worth_1m",
                        "text": "My net worth exceeds $1 million (excluding primary residence)",
                        "required": False
                    },
                    {
                        "id": "series_7_65_82",
                        "text": "I hold a Series 7, 65, or 82 license",
                        "required": False
                    }
                ],
                "note": "You may be asked to upload documentation before investing."
            }
        except Exception as e:
            # Return error message
            return {
                "error": f"Failed to load accreditation rules: {str(e)}",
                "jurisdiction": jurisdiction_code,
                "rules": [],
                "note": "You may be asked to upload documentation before investing."
            }
    
    @action(detail=False, methods=['get'])
    def accreditation_rules(self, request):
        """Get accreditation rules for a specific jurisdiction"""
        jurisdiction_code = request.query_params.get('jurisdiction', 'US')
        country = request.query_params.get('country', None)
        
        # If country is provided, map it to jurisdiction code
        if country:
            jurisdiction_code = self._get_jurisdiction_code(country)
        
        # Load rules
        rules_data = self._load_accreditation_rules(jurisdiction_code)
        
        return Response({
            'jurisdiction': jurisdiction_code,
            'country': country,
            'rules': rules_data
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



class InvestorProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the profile associated with the current user
        profile = get_object_or_404(InvestorProfile, user=request.user)
        
        serializer = InvestorOnboardingProgressSerializer(profile)
        
        # We can also add global status logic here to match your screenshot's "Almost Ready" text
        data = serializer.data
        
        # Determine overall status text for the UI header
        if data['completion_percentage'] == 100:
            status_message = "You're All Set!"
        elif data['completion_percentage'] > 0:
            status_message = "You're Almost Ready!"
        else:
            status_message = "Let's Get Started"

        return Response({
            "investor_id": profile.id,
            "status_message": status_message,
            "steps": data
        })