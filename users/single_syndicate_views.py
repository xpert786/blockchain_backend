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


class SingleSyndicateViewSet(viewsets.ViewSet):
    """
    Single API endpoint for complete syndicate creation with document uploads
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @action(detail=False, methods=['post'])
    def create_syndicate(self, request):
        """
        Create a complete syndicate with all data and documents in one API call
        POST /api/single-syndicate/create_syndicate/
        
        Content-Type: multipart/form-data
        
        Form Data:
        - Basic Info (text fields)
        - Team Members (JSON array)
        - Beneficiaries (JSON array)
        - Documents (files)
        - Compliance (boolean fields)
        """
        try:
            # Step 1: Create basic syndicate
            syndicate_data = {
                'name': request.data.get('name'),
                'description': request.data.get('description'),
                'accredited': request.data.get('accredited', 'No'),
                'manager': request.user,
                'lp_network': request.data.get('lp_network', ''),
                'enable_lp_network': request.data.get('enable_lp_network', 'No'),
                'firm_name': request.data.get('firm_name', ''),
                'Risk_Regulatory_Attestation': request.data.get('Risk_Regulatory_Attestation', ''),
                'jurisdictional_requirements': request.data.get('jurisdictional_requirements', ''),
                'additional_compliance_policies': request.data.get('additional_compliance_policies', ''),
            }
            
            # Validate required fields
            if not syndicate_data['name']:
                return Response({
                    'error': 'Syndicate name is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create syndicate
            syndicate = Syndicate.objects.create(**syndicate_data)
            
            # Step 2: Add sectors
            if 'sector_ids' in request.data:
                try:
                    sector_ids = request.data.get('sector_ids')
                    if isinstance(sector_ids, str):
                        # Handle comma-separated string
                        sector_ids = [int(x.strip()) for x in sector_ids.split(',') if x.strip()]
                    elif isinstance(sector_ids, list):
                        sector_ids = [int(x) for x in sector_ids]
                    
                    sectors = Sector.objects.filter(id__in=sector_ids)
                    syndicate.sectors.set(sectors)
                except (ValueError, TypeError) as e:
                    return Response({
                        'error': f'Invalid sector_ids format: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 3: Add geographies
            if 'geography_ids' in request.data:
                try:
                    geography_ids = request.data.get('geography_ids')
                    if isinstance(geography_ids, str):
                        # Handle comma-separated string
                        geography_ids = [int(x.strip()) for x in geography_ids.split(',') if x.strip()]
                    elif isinstance(geography_ids, list):
                        geography_ids = [int(x) for x in geography_ids]
                    
                    geographies = Geography.objects.filter(id__in=geography_ids)
                    syndicate.geographies.set(geographies)
                except (ValueError, TypeError) as e:
                    return Response({
                        'error': f'Invalid geography_ids format: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 4: Handle syndicate logo
            if 'syndicate_logo' in request.FILES:
                logo_file = request.FILES['syndicate_logo']
                syndicate.logo = logo_file
                syndicate.save()
                
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
            
            # Step 5: Handle team members
            if 'team_members' in request.data:
                try:
                    team_members_data = request.data.get('team_members')
                    if isinstance(team_members_data, str):
                        import json
                        team_members_data = json.loads(team_members_data)
                    
                    for member_data in team_members_data:
                        SyndicateTeamMember.objects.create(
                            syndicate=syndicate,
                            name=member_data['name'],
                            email=member_data['email'],
                            role=member_data['role'],
                            description=member_data.get('description', ''),
                            linkedin_profile=member_data.get('linkedin_profile', ''),
                            added_by=request.user
                        )
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    return Response({
                        'error': f'Invalid team_members format: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 6: Handle beneficiaries
            if 'beneficiaries' in request.data:
                try:
                    beneficiaries_data = request.data.get('beneficiaries')
                    if isinstance(beneficiaries_data, str):
                        import json
                        beneficiaries_data = json.loads(beneficiaries_data)
                    
                    for beneficiary_data in beneficiaries_data:
                        SyndicateBeneficiary.objects.create(
                            syndicate=syndicate,
                            name=beneficiary_data['name'],
                            email=beneficiary_data.get('email', ''),
                            relationship=beneficiary_data.get('relationship', ''),
                            ownership_percentage=beneficiary_data.get('ownership_percentage'),
                            added_by=request.user
                        )
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    return Response({
                        'error': f'Invalid beneficiaries format: {str(e)}'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 7: Handle document uploads
            document_types = [
                'company_certificate',
                'company_bank_statement',
                'company_proof_of_address',
                'beneficiary_government_id',
                'beneficiary_source_of_funds',
                'beneficiary_tax_id',
                'beneficiary_identity_document',
                'additional_policies'
            ]
            
            uploaded_documents = []
            for doc_type in document_types:
                if doc_type in request.FILES:
                    file = request.FILES[doc_type]
                    document = SyndicateDocument.objects.create(
                        syndicate=syndicate,
                        document_type=doc_type,
                        file=file,
                        original_filename=file.name,
                        file_size=file.size,
                        mime_type=file.content_type,
                        uploaded_by=request.user
                    )
                    uploaded_documents.append({
                        'document_type': doc_type,
                        'filename': file.name,
                        'size': file.size,
                        'mime_type': file.content_type
                    })
            
            # Step 8: Create compliance record
            compliance_data = {
                'syndicate': syndicate,
                'risk_regulatory_attestation': request.data.get('risk_regulatory_attestation', 'false').lower() == 'true',
                'jurisdictional_requirements': request.data.get('jurisdictional_requirements_check', 'false').lower() == 'true',
                'additional_compliance_policies': request.data.get('additional_compliance_policies_check', 'false').lower() == 'true',
                'self_knowledge_aml_policies': request.data.get('self_knowledge_aml_policies', 'false').lower() == 'true',
                'is_regulated_entity': request.data.get('is_regulated_entity', 'false').lower() == 'true',
                'is_ml_tf_risk': request.data.get('is_ml_tf_risk', 'false').lower() == 'true',
                'attestation_text': request.data.get('attestation_text', ''),
                'attested_by': request.user
            }
            
            SyndicateCompliance.objects.create(**compliance_data)
            
            # Step 9: Prepare response
            team_members = SyndicateTeamMember.objects.filter(syndicate=syndicate)
            beneficiaries = SyndicateBeneficiary.objects.filter(syndicate=syndicate)
            documents = SyndicateDocument.objects.filter(syndicate=syndicate)
            compliance = SyndicateCompliance.objects.filter(syndicate=syndicate).first()
            
            response_data = {
                'success': True,
                'message': 'Syndicate created successfully!',
                'syndicate_id': syndicate.id,
                'submission_id': f"SYN-{syndicate.id}-{uuid.uuid4().hex[:8].upper()}",
                'syndicate': {
                    'id': syndicate.id,
                    'name': syndicate.name,
                    'description': syndicate.description,
                    'accredited': syndicate.accredited,
                    'firm_name': syndicate.firm_name,
                    'manager': syndicate.manager.username,
                    'sectors': [sector.name for sector in syndicate.sectors.all()],
                    'geographies': [geo.name for geo in syndicate.geographies.all()],
                    'lp_network': syndicate.lp_network,
                    'enable_lp_network': syndicate.enable_lp_network,
                    'created_at': syndicate.time_of_register
                },
                'team_members': [
                    {
                        'name': member.name,
                        'email': member.email,
                        'role': member.role,
                        'description': member.description
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
                        'filename': doc.original_filename,
                        'size': doc.file_size,
                        'mime_type': doc.mime_type,
                        'uploaded_at': doc.uploaded_at
                    } for doc in documents
                ],
                'compliance': {
                    'risk_regulatory_attestation': compliance.risk_regulatory_attestation if compliance else False,
                    'jurisdictional_requirements': compliance.jurisdictional_requirements if compliance else False,
                    'additional_compliance_policies': compliance.additional_compliance_policies if compliance else False,
                    'self_knowledge_aml_policies': compliance.self_knowledge_aml_policies if compliance else False,
                    'is_regulated_entity': compliance.is_regulated_entity if compliance else False,
                    'is_ml_tf_risk': compliance.is_ml_tf_risk if compliance else False,
                    'attested_at': compliance.attested_at if compliance else None
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': f'Failed to create syndicate: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def get_syndicate(self, request):
        """
        Get syndicate details by ID
        GET /api/single-syndicate/get_syndicate/?syndicate_id=1
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
        
        # Get all related data
        team_members = SyndicateTeamMember.objects.filter(syndicate=syndicate)
        beneficiaries = SyndicateBeneficiary.objects.filter(syndicate=syndicate)
        documents = SyndicateDocument.objects.filter(syndicate=syndicate)
        compliance = SyndicateCompliance.objects.filter(syndicate=syndicate).first()
        
        response_data = {
            'syndicate': {
                'id': syndicate.id,
                'name': syndicate.name,
                'description': syndicate.description,
                'accredited': syndicate.accredited,
                'firm_name': syndicate.firm_name,
                'manager': syndicate.manager.username,
                'sectors': [sector.name for sector in syndicate.sectors.all()],
                'geographies': [geo.name for geo in syndicate.geographies.all()],
                'lp_network': syndicate.lp_network,
                'enable_lp_network': syndicate.enable_lp_network,
                'created_at': syndicate.time_of_register
            },
            'team_members': [
                {
                    'name': member.name,
                    'email': member.email,
                    'role': member.role,
                    'description': member.description
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
                    'filename': doc.original_filename,
                    'size': doc.file_size,
                    'mime_type': doc.mime_type,
                    'uploaded_at': doc.uploaded_at
                } for doc in documents
            ],
            'compliance': {
                'risk_regulatory_attestation': compliance.risk_regulatory_attestation if compliance else False,
                'jurisdictional_requirements': compliance.jurisdictional_requirements if compliance else False,
                'additional_compliance_policies': compliance.additional_compliance_policies if compliance else False,
                'self_knowledge_aml_policies': compliance.self_knowledge_aml_policies if compliance else False,
                'is_regulated_entity': compliance.is_regulated_entity if compliance else False,
                'is_ml_tf_risk': compliance.is_ml_tf_risk if compliance else False,
                'attested_at': compliance.attested_at if compliance else None
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
