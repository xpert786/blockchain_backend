from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import uuid

from .models import CustomUser, Syndicate, Sector, Geography
from .syndicate_document_models import SyndicateDocument, SyndicateTeamMember, SyndicateBeneficiary, SyndicateCompliance
from .serializers import SyndicateSerializer


class SyndicateFlowViewSet(viewsets.ViewSet):
    """
    Multi-step syndicate creation flow with document uploads
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @action(detail=False, methods=['post'])
    def step1_lead_info(self, request):
        """
        Step 1: Lead Info - Basic syndicate information
        POST /api/syndicate-flow/step1_lead_info/
        """
        data = request.data
        
        # Validate required fields
        required_fields = ['name', 'description', 'accredited']
        for field in required_fields:
            if field not in data:
                return Response({
                    'error': f'Field "{field}" is required'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create syndicate with basic info
            syndicate_data = {
                'name': data['name'],
                'description': data['description'],
                'accredited': data['accredited'],
                'manager': request.user,
                'lp_network': data.get('lp_network', ''),
                'enable_lp_network': data.get('enable_lp_network', 'No')
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
            
            return Response({
                'success': True,
                'message': 'Step 1 completed successfully',
                'syndicate_id': syndicate.id,
                'syndicate': SyndicateSerializer(syndicate).data,
                'next_step': 'step2_entity_profile'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def step2_entity_profile(self, request):
        """
        Step 2: Entity Profile - Firm details and team members
        POST /api/syndicate-flow/step2_entity_profile/
        """
        syndicate_id = request.data.get('syndicate_id')
        
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id, manager=request.user)
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Update syndicate with entity profile data
            if 'firm_name' in request.data:
                syndicate.firm_name = request.data['firm_name']
            
            # Handle syndicate logo upload
            if 'syndicate_logo' in request.FILES:
                logo_file = request.FILES['syndicate_logo']
                syndicate.logo = logo_file
                
                # Also save as document for tracking
                SyndicateDocument.objects.create(
                    syndicate=syndicate,
                    document_type='syndicate_logo',
                    file=logo_file,
                    original_filename=logo_file.name,
                    file_size=logo_file.size,
                    mime_type=logo_file.content_type,
                    uploaded_by=request.user
                )
            
            syndicate.save()
            
            # Handle team members
            if 'team_members' in request.data:
                # Clear existing team members
                SyndicateTeamMember.objects.filter(syndicate=syndicate).delete()
                
                # Add new team members
                for member_data in request.data['team_members']:
                    SyndicateTeamMember.objects.create(
                        syndicate=syndicate,
                        name=member_data['name'],
                        email=member_data['email'],
                        role=member_data['role'],
                        description=member_data.get('description', ''),
                        linkedin_profile=member_data.get('linkedin_profile', ''),
                        added_by=request.user
                    )
            
            return Response({
                'success': True,
                'message': 'Step 2 completed successfully',
                'syndicate_id': syndicate.id,
                'syndicate': SyndicateSerializer(syndicate).data,
                'next_step': 'step3_kyb_verification'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def step3_kyb_verification(self, request):
        """
        Step 3: KYB Verification - Company and beneficiary documents
        POST /api/syndicate-flow/step3_kyb_verification/
        """
        syndicate_id = request.data.get('syndicate_id')
        
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id, manager=request.user)
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Handle company documents
            company_docs = [
                'company_certificate',
                'company_bank_statement',
                'company_proof_of_address'
            ]
            
            for doc_type in company_docs:
                if doc_type in request.FILES:
                    file = request.FILES[doc_type]
                    SyndicateDocument.objects.create(
                        syndicate=syndicate,
                        document_type=doc_type,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        mime_type=file.content_type,
                        uploaded_by=request.user
                    )
            
            # Handle beneficiary documents
            beneficiary_docs = [
                'beneficiary_government_id',
                'beneficiary_source_of_funds',
                'beneficiary_tax_id',
                'beneficiary_identity_document'
            ]
            
            for doc_type in beneficiary_docs:
                if doc_type in request.FILES:
                    file = request.FILES[doc_type]
                    SyndicateDocument.objects.create(
                        syndicate=syndicate,
                        document_type=doc_type,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        mime_type=file.content_type,
                        uploaded_by=request.user
                    )
            
            # Handle beneficiaries
            if 'beneficiaries' in request.data:
                # Clear existing beneficiaries
                SyndicateBeneficiary.objects.filter(syndicate=syndicate).delete()
                
                # Add new beneficiaries
                for beneficiary_data in request.data['beneficiaries']:
                    SyndicateBeneficiary.objects.create(
                        syndicate=syndicate,
                        name=beneficiary_data['name'],
                        email=beneficiary_data.get('email', ''),
                        relationship=beneficiary_data.get('relationship', ''),
                        ownership_percentage=beneficiary_data.get('ownership_percentage'),
                        added_by=request.user
                    )
            
            return Response({
                'success': True,
                'message': 'Step 3 completed successfully',
                'syndicate_id': syndicate.id,
                'next_step': 'step4_compliance'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def step4_compliance(self, request):
        """
        Step 4: Compliance & Attestation
        POST /api/syndicate-flow/step4_compliance/
        """
        syndicate_id = request.data.get('syndicate_id')
        
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id, manager=request.user)
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Update syndicate compliance fields
            if 'Risk_Regulatory_Attestation' in request.data:
                syndicate.Risk_Regulatory_Attestation = request.data['Risk_Regulatory_Attestation']
            if 'jurisdictional_requirements' in request.data:
                syndicate.jurisdictional_requirements = request.data['jurisdictional_requirements']
            if 'additional_compliance_policies' in request.data:
                syndicate.additional_compliance_policies = request.data['additional_compliance_policies']
            
            syndicate.save()
            
            # Handle additional compliance documents
            if 'additional_policies' in request.FILES:
                file = request.FILES['additional_policies']
                SyndicateDocument.objects.create(
                    syndicate=syndicate,
                    document_type='additional_policies',
                    file=file,
                    original_filename=file.name,
                    file_size=file.size,
                    mime_type=file.content_type,
                    uploaded_by=request.user
                )
            
            # Create compliance record
            compliance_data = {
                'syndicate': syndicate,
                'risk_regulatory_attestation': request.data.get('risk_regulatory_attestation', False),
                'jurisdictional_requirements': request.data.get('jurisdictional_requirements_check', False),
                'additional_compliance_policies': request.data.get('additional_compliance_policies_check', False),
                'self_knowledge_aml_policies': request.data.get('self_knowledge_aml_policies', False),
                'is_regulated_entity': request.data.get('is_regulated_entity', False),
                'is_ml_tf_risk': request.data.get('is_ml_tf_risk', False),
                'attestation_text': request.data.get('attestation_text', ''),
                'attested_by': request.user
            }
            
            SyndicateCompliance.objects.create(**compliance_data)
            
            return Response({
                'success': True,
                'message': 'Step 4 completed successfully',
                'syndicate_id': syndicate.id,
                'next_step': 'step5_final_review'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def step5_final_review(self, request):
        """
        Step 5: Final Review & Submit
        POST /api/syndicate-flow/step5_final_review/
        """
        syndicate_id = request.data.get('syndicate_id')
        
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id, manager=request.user)
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Get all related data for final review
            team_members = SyndicateTeamMember.objects.filter(syndicate=syndicate)
            beneficiaries = SyndicateBeneficiary.objects.filter(syndicate=syndicate)
            documents = SyndicateDocument.objects.filter(syndicate=syndicate)
            compliance = SyndicateCompliance.objects.filter(syndicate=syndicate).first()
            
            # Prepare final review data
            review_data = {
                'syndicate': SyndicateSerializer(syndicate).data,
                'team_members': [
                    {
                        'name': member.name,
                        'email': member.email,
                        'role': member.role,
                        'description': member.description,
                        'linkedin_profile': member.linkedin_profile
                    } for member in team_members
                ],
                'beneficiaries': [
                    {
                        'name': beneficiary.name,
                        'email': beneficiary.email,
                        'relationship': beneficiary.relationship,
                        'ownership_percentage': beneficiary.ownership_percentage
                    } for beneficiary in beneficiaries
                ],
                'documents': [
                    {
                        'document_type': doc.document_type,
                        'original_filename': doc.original_filename,
                        'file_size': doc.file_size,
                        'mime_type': doc.mime_type,
                        'uploaded_at': doc.uploaded_at,
                        'is_verified': doc.is_verified
                    } for doc in documents
                ],
                'compliance': {
                    'risk_regulatory_attestation': compliance.risk_regulatory_attestation if compliance else False,
                    'jurisdictional_requirements': compliance.jurisdictional_requirements if compliance else False,
                    'additional_compliance_policies': compliance.additional_compliance_policies if compliance else False,
                    'self_knowledge_aml_policies': compliance.self_knowledge_aml_policies if compliance else False,
                    'is_regulated_entity': compliance.is_regulated_entity if compliance else False,
                    'is_ml_tf_risk': compliance.is_ml_tf_risk if compliance else False,
                    'attestation_text': compliance.attestation_text if compliance else '',
                    'attested_at': compliance.attested_at if compliance else None
                }
            }
            
            return Response({
                'success': True,
                'message': 'Final review data prepared successfully',
                'review_data': review_data,
                'next_step': 'submit'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def submit_syndicate(self, request):
        """
        Submit the syndicate application
        POST /api/syndicate-flow/submit_syndicate/
        """
        syndicate_id = request.data.get('syndicate_id')
        
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id, manager=request.user)
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        try:
            # Mark syndicate as submitted (you might want to add a status field)
            # For now, we'll just return success
            
            return Response({
                'success': True,
                'message': 'Syndicate application submitted successfully!',
                'syndicate': SyndicateSerializer(syndicate).data,
                'submission_id': f"SYN-{syndicate.id}-{uuid.uuid4().hex[:8].upper()}"
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def get_syndicate_progress(self, request):
        """
        Get syndicate creation progress
        GET /api/syndicate-flow/get_syndicate_progress/?syndicate_id=1
        """
        syndicate_id = request.query_params.get('syndicate_id')
        
        if not syndicate_id:
            return Response({
                'error': 'syndicate_id parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            syndicate = Syndicate.objects.get(id=syndicate_id, manager=request.user)
        except Syndicate.DoesNotExist:
            return Response({
                'error': 'Syndicate not found or access denied'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check progress based on completed steps
        progress = {
            'step1_completed': bool(syndicate.name and syndicate.description),
            'step2_completed': bool(syndicate.firm_name),
            'step3_completed': SyndicateDocument.objects.filter(syndicate=syndicate).exists(),
            'step4_completed': SyndicateCompliance.objects.filter(syndicate=syndicate).exists(),
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
