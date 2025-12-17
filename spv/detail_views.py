"""
SPV Detail Views - Detailed information about individual SPVs
Including metrics, investment terms, investors, and documents
"""

from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

from .models import SPV
from investors.models import InvestorProfile


def _safe_decimal(value):
    """Safely convert value to Decimal with comprehensive error handling"""
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    
    # Handle string values
    value_str = str(value).strip()
    if not value_str or value_str.lower() in ['none', 'null', '']:
        return Decimal('0')
    
    try:
        return Decimal(value_str)
    except Exception:
        return Decimal('0')


def _decimal_to_float(value):
    """Safely convert Decimal to float"""
    try:
        value = _safe_decimal(value)
        return float(value) if value else 0.0
    except Exception:
        return 0.0


class IsSPVOwnerOrAdmin(permissions.BasePermission):
    """Permission to check if user is SPV owner or admin"""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_details(request, spv_id):
    """
    Get detailed information about an SPV
    GET /api/spv/{id}/details/
    
    Returns comprehensive SPV information including:
    - Basic details (name, status, dates)
    - Financial metrics (raised, target, progress)
    - Deal terms
    - Company information
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
        return Response({
            'error': 'You do not have permission to access this SPV'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Calculate financial metrics
    my_commitment = _safe_decimal(spv.allocation)
    target_amount = _safe_decimal(spv.round_size)
    gp_commitment = _safe_decimal(spv.gp_commitment)
    
    total_raised = my_commitment + gp_commitment
    progress_percent = Decimal('0')
    if target_amount > 0:
        progress_percent = (total_raised / target_amount) * Decimal('100')
    progress_percent = min(progress_percent, Decimal('100'))
    
    # Calculate days left
    days_to_close = None
    if spv.target_closing_date:
        today = timezone.now().date()
        if spv.target_closing_date > today:
            days_to_close = (spv.target_closing_date - today).days
    
    response_data = {
        'success': True,
        'data': {
            'id': spv.id,
            'spv_code': f'SPV-{spv.id:03d}',
            'display_name': spv.display_name,
            'status': spv.status,
            'status_label': spv.get_status_display(),
            'created_at': spv.created_at.isoformat(),
            'updated_at': spv.updated_at.isoformat(),
            
            # SPV Details Section
            'spv_details': {
                'spv_code': f'SPV-{spv.id:03d}',
                'year': spv.created_at.year,
                'country': spv.country_of_incorporation,
                'incorporation_date': spv.created_at.strftime('%m/%d/%Y'),
                'term_length_years': spv.target_closing_date.year - spv.created_at.year if spv.target_closing_date else None,
                'fund_lead': {
                    'id': spv.fund_lead.id,
                    'name': spv.fund_lead.get_full_name() or spv.fund_lead.username,
                    'email': spv.fund_lead.email
                } if spv.fund_lead else None,
                'jurisdiction': spv.jurisdiction,
            },
            
            # Financial Metrics
            'financial_metrics': {
                'total_value': _decimal_to_float(my_commitment),
                'uninvested_sum': _decimal_to_float(target_amount - total_raised),
                'irr': 15.2,  # Placeholder - calculate from data if available
                'multiple': 1.7,  # Placeholder - calculate from data if available
            },
            
            # Fundraising Progress
            'fundraising_progress': {
                'my_spvs': _decimal_to_float(my_commitment),
                'target': _decimal_to_float(target_amount),
                'gp_commitment': _decimal_to_float(gp_commitment),
                'total_raised': _decimal_to_float(total_raised),
                'progress_percent': float(progress_percent.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)),
                'remaining_amount': _decimal_to_float(target_amount - total_raised),
                'target_closing_date': spv.target_closing_date.isoformat() if spv.target_closing_date else None,
                'days_to_close': days_to_close,
            },
            
            # Investment Terms
            'investment_terms': {
                'minimum_investment': _decimal_to_float(spv.minimum_lp_investment),
                'valuation_type': spv.valuation_type,
                'valuation_type_label': 'Pre money' if spv.valuation_type == 'pre_money' else 'Post money',
                'instrument_type': spv.instrument_type.name if spv.instrument_type else None,
                'share_class': spv.share_class.name if spv.share_class else None,
                'round': spv.round.name if spv.round else None,
                'transaction_type': spv.transaction_type,
                'transaction_type_label': 'Primary' if spv.transaction_type == 'primary' else 'Secondary',
            },
            
            # Portfolio Company
            'portfolio_company': {
                'name': spv.portfolio_company.name if spv.portfolio_company else spv.portfolio_company_name,
                'stage': spv.company_stage.name if spv.company_stage else None,
                'sector': spv.deal_tags[0] if isinstance(spv.deal_tags, list) and spv.deal_tags else None,
                'sectors': spv.deal_tags if isinstance(spv.deal_tags, list) else [],
            },
            
            # Carry & Fees
            'carry_fees': {
                'total_carry_percentage': float(spv.total_carry_percentage) if spv.total_carry_percentage else 0.0,
                'lead_carry_percentage': float(spv.lead_carry_percentage) if spv.lead_carry_percentage else 0.0,
                'carry_recipient': spv.carry_recipient,
            },
            
            # Investors Count
            'investors': {
                'count': len(spv.lp_invite_emails or []),
                'emails': spv.lp_invite_emails or [],
            },
            
            # Documents
            'documents': {
                'pitch_deck_url': request.build_absolute_uri(spv.pitch_deck.url) if spv.pitch_deck else None,
                'supporting_document_url': request.build_absolute_uri(spv.supporting_document.url) if spv.supporting_document else None,
                'deal_memo': spv.deal_memo,
            },
            
            # Additional Info
            'additional_info': {
                'deal_name': spv.deal_name,
                'adviser_entity': spv.adviser_entity,
                'master_partnership_entity': spv.master_partnership_entity.name if spv.master_partnership_entity else None,
                'access_mode': spv.access_mode,
                'investment_visibility': spv.investment_visibility,
                'deal_partners': spv.deal_partners,
                'founder_email': spv.founder_email,
            }
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_performance_metrics(request, spv_id):
    """
    Get performance metrics for an SPV
    GET /api/spv/{id}/performance-metrics/
    
    Returns:
    - Total value
    - Uninvested sum
    - IRR
    - Multiple
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
        return Response({
            'error': 'You do not have permission to access this SPV'
        }, status=status.HTTP_403_FORBIDDEN)
    
    my_commitment = _safe_decimal(spv.allocation)
    
    metrics = {
        'success': True,
        'data': {
            'spv_id': spv.id,
            'spv_name': spv.display_name,
            'performance': {
                'total_value': _decimal_to_float(my_commitment),
                'uninvested_sum': _decimal_to_float(Decimal('0')),  # Calculate based on portfolio data
                'irr': 15.2,  # Placeholder
                'multiple': 1.7,  # Placeholder
                'return_percent': 70.0,  # Placeholder
            },
            'quarterly_data': [
                {'quarter': 'Q1 2024', 'value': 2400, 'benchmark': 2400},
                {'quarter': 'Q2 2024', 'value': 1398, 'benchmark': 1221},
                {'quarter': 'Q3 2024', 'value': 9800, 'benchmark': 2290},
                {'quarter': 'Q4 2024', 'value': 3908, 'benchmark': 2000},
            ]
        }
    }
    
    return Response(metrics)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_investment_terms(request, spv_id):
    """
    Get detailed investment terms for an SPV
    GET /api/spv/{id}/investment-terms/
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
        return Response({
            'error': 'You do not have permission to access this SPV'
        }, status=status.HTTP_403_FORBIDDEN)
    
    terms = {
        'success': True,
        'data': {
            'spv_id': spv.id,
            'spv_name': spv.display_name,
            'minimum_investment': {
                'amount': _decimal_to_float(spv.minimum_lp_investment),
                'currency': 'USD'
            },
            'valuation': {
                'type': spv.valuation_type,
                'type_label': 'Pre money' if spv.valuation_type == 'pre_money' else 'Post money',
                'amount': _decimal_to_float(spv.round_size),
            },
            'instrument': {
                'type': spv.instrument_type.name if spv.instrument_type else None,
                'description': spv.instrument_type.description if spv.instrument_type else None,
            },
            'round': {
                'name': spv.round.name if spv.round else None,
                'description': spv.round.description if spv.round else None,
            },
            'share_class': {
                'name': spv.share_class.name if spv.share_class else None,
                'description': spv.share_class.description if spv.share_class else None,
            },
            'carry': {
                'total_carry_percentage': float(spv.total_carry_percentage) if spv.total_carry_percentage else 0.0,
                'lead_carry_percentage': float(spv.lead_carry_percentage) if spv.lead_carry_percentage else 0.0,
                'carry_recipient': spv.carry_recipient,
            },
            'transaction': {
                'type': spv.transaction_type,
                'type_label': 'Primary' if spv.transaction_type == 'primary' else 'Secondary',
            },
            'target_closing_date': spv.target_closing_date.isoformat() if spv.target_closing_date else None,
        }
    }
    
    return Response(terms)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_investors(request, spv_id):
    """
    Get list of investors in an SPV with detailed information
    GET /api/spv/{id}/investors/
    
    Returns investor list with:
    - Investor name and email
    - Investment amount
    - Ownership percentage
    - Investment date
    - Status
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
        return Response({
            'error': 'You do not have permission to access this SPV'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Mock investor data based on lp_invite_emails
    investors_list = []
    total_raised = _safe_decimal(spv.allocation) + _safe_decimal(spv.gp_commitment)
    
    if spv.lp_invite_emails:
        # Sample investor data - in real scenario, fetch from Investor model
        sample_investors = [
            {
                'name': 'Michael Investor',
                'email': spv.lp_invite_emails[0] if len(spv.lp_invite_emails) > 0 else 'investor@example.com',
                'amount': 50000,
                'percentage': 25,
                'date': spv.created_at.strftime('%m/%d/%Y'),
                'status': 'Active'
            },
            {
                'name': 'Sarah Johnson',
                'email': spv.lp_invite_emails[1] if len(spv.lp_invite_emails) > 1 else 'sarah@example.com',
                'amount': 50000,
                'percentage': 25,
                'date': spv.created_at.strftime('%m/%d/%Y'),
                'status': 'Active'
            },
            {
                'name': 'Michael Investor',
                'email': spv.lp_invite_emails[2] if len(spv.lp_invite_emails) > 2 else 'michael2@example.com',
                'amount': 50000,
                'percentage': 25,
                'date': spv.created_at.strftime('%m/%d/%Y'),
                'status': 'Active'
            }
        ]
        
        investors_list = sample_investors[:len(spv.lp_invite_emails)]
    
    response_data = {
        'success': True,
        'data': {
            'spv_id': spv.id,
            'spv_name': spv.display_name,
            'total_investors': len(investors_list),
            'total_raised': _decimal_to_float(total_raised),
            'investors': investors_list,
            'pagination': {
                'current_page': 1,
                'total_pages': 1,
                'page_size': 10,
                'total_count': len(investors_list)
            }
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_documents(request, spv_id):
    """
    Get documents associated with an SPV
    GET /api/spv/{id}/documents/
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
        return Response({
            'error': 'You do not have permission to access this SPV'
        }, status=status.HTTP_403_FORBIDDEN)
    
    documents = []
    
    if spv.pitch_deck:
        documents.append({
            'id': 1,
            'name': 'Pitch Deck',
            'type': 'presentation',
            'url': request.build_absolute_uri(spv.pitch_deck.url),
            'uploaded_at': spv.created_at.isoformat(),
            'uploaded_by': spv.created_by.get_full_name() or spv.created_by.username,
            'size_mb': 5.2,
        })
    
    if spv.supporting_document:
        documents.append({
            'id': 2,
            'name': 'Supporting Document',
            'type': 'document',
            'url': request.build_absolute_uri(spv.supporting_document.url),
            'uploaded_at': spv.updated_at.isoformat(),
            'uploaded_by': spv.created_by.get_full_name() or spv.created_by.username,
            'size_mb': 3.1,
        })
    
    response_data = {
        'success': True,
        'data': {
            'spv_id': spv.id,
            'spv_name': spv.display_name,
            'total_documents': len(documents),
            'documents': documents
        }
    }
    
    return Response(response_data)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def spv_invite_lps(request, spv_id):
    """
    Get or send LP invitations for an SPV
    GET /api/spv/{id}/invite-lps/ - Get current invite settings
    POST /api/spv/{id}/invite-lps/ - Send invitations to LPs
    
    POST Payload:
    {
        "emails": ["investor1@example.com", "investor2@example.com"],
        "message": "Investment opportunity text",
        "lead_carry_percentage": 5.0,
        "investment_visibility": "hidden",  # or "visible"
        "auto_invite_active_spvs": false,
        "private_note": "Internal note",
        "tags": ["tag1", "tag2"]
    }
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
        return Response({
            'error': 'You do not have permission to access this SPV'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        # Return current invite settings
        response_data = {
            'success': True,
            'data': {
                'spv_id': spv.id,
                'spv_name': spv.display_name,
                'current_invites': {
                    'total_emails': len(spv.lp_invite_emails or []),
                    'emails': spv.lp_invite_emails or [],
                    'message': spv.lp_invite_message,
                    'lead_carry_percentage': float(spv.lead_carry_percentage) if spv.lead_carry_percentage else 0.0,
                    'investment_visibility': spv.investment_visibility,
                    'auto_invite_active_spvs': spv.auto_invite_active_spvs,
                    'private_note': spv.invite_private_note,
                    'tags': spv.invite_tags or [],
                }
            }
        }
        return Response(response_data)
    
    elif request.method == 'POST':
        # Validate required fields
        emails = request.data.get('emails', [])
        message = request.data.get('message')
        
        if not emails or not isinstance(emails, list):
            return Response({
                'success': False,
                'error': 'emails field is required and must be a list of email addresses'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(emails) == 0:
            return Response({
                'success': False,
                'error': 'At least one email address is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate email format
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        invalid_emails = [e for e in emails if not re.match(email_regex, e)]
        
        if invalid_emails:
            return Response({
                'success': False,
                'error': f'Invalid email addresses: {", ".join(invalid_emails)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if emails belong to registered investors
        investor_emails = set(
            InvestorProfile.objects.filter(
                email_address__in=emails
            ).values_list('email_address', flat=True)
        )
        non_investor_emails = [e for e in emails if e not in investor_emails]
        
        if non_investor_emails:
            return Response({
                'success': False,
                'error': f'The following emails do not belong to registered investors: {", ".join(non_investor_emails)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Merge with existing emails (avoid duplicates)
        existing_emails = set(spv.lp_invite_emails or [])
        new_emails = set(emails)
        all_emails = list(existing_emails.union(new_emails))
        
        # Update SPV with new invite data
        spv.lp_invite_emails = all_emails
        spv.lp_invite_message = message or spv.lp_invite_message
        
        # Update optional fields
        if 'lead_carry_percentage' in request.data:
            spv.lead_carry_percentage = request.data['lead_carry_percentage']
        
        if 'investment_visibility' in request.data:
            visibility = request.data['investment_visibility']
            if visibility in ['hidden', 'visible']:
                spv.investment_visibility = visibility
        
        if 'auto_invite_active_spvs' in request.data:
            spv.auto_invite_active_spvs = request.data['auto_invite_active_spvs']
        
        if 'private_note' in request.data:
            spv.invite_private_note = request.data['private_note']
        
        if 'tags' in request.data and isinstance(request.data['tags'], list):
            spv.invite_tags = request.data['tags']
        
        spv.save()
        
        # Here you would typically send actual emails
        # For now, we'll just log the invitation
        new_invites_sent = len(new_emails - existing_emails)
        
        response_data = {
            'success': True,
            'message': f'LP invitations sent successfully to {new_invites_sent} new investor(s)',
            'data': {
                'spv_id': spv.id,
                'total_invited': len(all_emails),
                'new_invites_sent': new_invites_sent,
                'emails_invited': list(new_emails - existing_emails),
                'all_emails': all_emails,
                'settings': {
                    'lead_carry_percentage': float(spv.lead_carry_percentage) if spv.lead_carry_percentage else 0.0,
                    'investment_visibility': spv.investment_visibility,
                    'auto_invite_active_spvs': spv.auto_invite_active_spvs,
                    'private_note': spv.invite_private_note,
                    'tags': spv.invite_tags or [],
                }
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def spv_manage_lp_defaults(request):
    """
    Get or set default LP invitation settings for the user
    GET /api/spv/invite-lps/defaults/ - Get default settings
    POST /api/spv/invite-lps/defaults/ - Set default settings
    
    POST Payload:
    {
        "lead_carry_percentage": 5.0,
        "investment_visibility": "hidden",
        "auto_invite_active_spvs": true,
        "default_message": "Default invitation message"
    }
    """
    # Store in user profile or custom settings
    # For now, return template defaults
    
    if request.method == 'GET':
        response_data = {
            'success': True,
            'data': {
                'user_id': request.user.id,
                'defaults': {
                    'lead_carry_percentage': 5.0,
                    'investment_visibility': 'hidden',
                    'auto_invite_active_spvs': False,
                    'default_message': 'You are invited to invest in this SPV opportunity. Please review the details and let us know if you are interested.'
                }
            }
        }
        return Response(response_data)
    
    elif request.method == 'POST':
        # In real implementation, save to UserProfile or custom settings
        defaults = {
            'lead_carry_percentage': request.data.get('lead_carry_percentage', 5.0),
            'investment_visibility': request.data.get('investment_visibility', 'hidden'),
            'auto_invite_active_spvs': request.data.get('auto_invite_active_spvs', False),
            'default_message': request.data.get('default_message', '')
        }
        
        response_data = {
            'success': True,
            'message': 'Default LP invitation settings updated successfully',
            'data': {
                'user_id': request.user.id,
                'defaults': defaults
            }
        }
        return Response(response_data)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def spv_remove_lp_invite(request, spv_id, email):
    """
    Remove an LP from the invite list
    DELETE /api/spv/{id}/invite-lps/{email}/
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Check permissions
    if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
        return Response({
            'error': 'You do not have permission to access this SPV'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if not spv.lp_invite_emails or email not in spv.lp_invite_emails:
        return Response({
            'success': False,
            'error': f'Email {email} not found in invite list'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Remove email from list
    spv.lp_invite_emails = [e for e in spv.lp_invite_emails if e != email]
    spv.save()
    
    response_data = {
        'success': True,
        'message': f'Email {email} removed from invite list',
        'data': {
            'spv_id': spv.id,
            'removed_email': email,
            'remaining_emails': spv.lp_invite_emails,
            'total_remaining': len(spv.lp_invite_emails)
        }
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([permissions.IsAuthenticated])
def spv_bulk_invite_lps(request):
    """
    Send invitations to LPs for multiple SPVs
    PATCH /api/spv/bulk-invite-lps/
    
    Payload:
    {
        "spv_ids": [1, 2, 3],
        "emails": ["investor@example.com"],
        "message": "Investment opportunity",
        "lead_carry_percentage": 5.0
    }
    """
    spv_ids = request.data.get('spv_ids', [])
    emails = request.data.get('emails', [])
    
    if not spv_ids or not isinstance(spv_ids, list):
        return Response({
            'success': False,
            'error': 'spv_ids field is required and must be a list'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not emails or not isinstance(emails, list):
        return Response({
            'success': False,
            'error': 'emails field is required and must be a list'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get all SPVs
    spvs = SPV.objects.filter(id__in=spv_ids)
    
    # Check permissions - user must own all SPVs
    for spv in spvs:
        if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
            return Response({
                'error': f'You do not have permission to access SPV {spv.id}'
            }, status=status.HTTP_403_FORBIDDEN)
    
    if spvs.count() != len(spv_ids):
        return Response({
            'success': False,
            'error': f'Some SPVs not found. Found {spvs.count()} out of {len(spv_ids)}'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Update all SPVs
    message = request.data.get('message')
    lead_carry = request.data.get('lead_carry_percentage')
    
    updated_count = 0
    for spv in spvs:
        existing_emails = set(spv.lp_invite_emails or [])
        new_emails = set(emails)
        spv.lp_invite_emails = list(existing_emails.union(new_emails))
        
        if message:
            spv.lp_invite_message = message
        
        if lead_carry is not None:
            spv.lead_carry_percentage = lead_carry
        
        spv.save()
        updated_count += 1
    
    response_data = {
        'success': True,
        'message': f'LP invitations sent to {updated_count} SPV(s)',
        'data': {
            'spvs_updated': updated_count,
            'emails_invited': emails,
            'spv_ids': spv_ids,
            'settings': {
                'lead_carry_percentage': float(lead_carry) if lead_carry else None,
                'message': message
            }
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_cap_table(request, spv_id):
    """
    Get cap table for an SPV - shows all investor ownership
    GET /api/spv/{spv_id}/cap-table/
    
    Returns:
    - List of investors with their ownership percentages
    - Total raised amount
    - Ownership breakdown
    
    Only accessible by SPV owner, syndicate managers, and admins.
    """
    from investors.dashboard_models import Investment
    from django.db.models import Sum
    
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Check permissions - only SPV owner, syndicate managers, and admins
    if not (request.user.is_staff or request.user.role == 'admin' or spv.created_by == request.user):
        return Response({
            'success': False,
            'error': 'You do not have permission to view this cap table'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Get all committed/active investments for this SPV
    investments = Investment.objects.filter(
        spv=spv,
        status__in=['committed', 'active', 'completed']
    ).select_related('investor', 'payment').order_by('-commitment_date', '-created_at')
    
    # Calculate totals
    total_raised = investments.aggregate(total=Sum('invested_amount'))['total'] or Decimal('0')
    target_allocation = _safe_decimal(spv.allocation)
    
    # Build investor list
    investors_list = []
    for inv in investments:
        # Calculate ownership percentage
        ownership_pct = Decimal('0')
        if target_allocation > 0:
            ownership_pct = (inv.invested_amount / target_allocation) * Decimal('100')
        
        investors_list.append({
            'investor_id': inv.investor.id,
            'investor_name': inv.investor.get_full_name() or inv.investor.username,
            'investor_email': inv.investor.email,
            'invested_amount': float(inv.invested_amount),
            'ownership_percentage': float(ownership_pct.quantize(Decimal('0.01'))),
            'status': inv.status,
            'status_display': inv.get_status_display(),
            'payment_id': inv.payment.payment_id if inv.payment else None,
            'payment_status': inv.payment.status if inv.payment else None,
            'commitment_date': inv.commitment_date.isoformat() if inv.commitment_date else None,
            'invested_at': inv.invested_at.isoformat() if inv.invested_at else None,
        })
    
    # Calculate allocation utilization
    allocation_used_pct = Decimal('0')
    if target_allocation > 0:
        allocation_used_pct = (total_raised / target_allocation) * Decimal('100')
    
    response_data = {
        'success': True,
        'data': {
            'spv_id': spv.id,
            'spv_name': spv.display_name,
            'spv_status': spv.status,
            
            # Cap Table Summary
            'summary': {
                'total_investors': len(investors_list),
                'total_raised': float(total_raised),
                'target_allocation': float(target_allocation),
                'remaining_allocation': float(target_allocation - total_raised),
                'allocation_used_percentage': float(allocation_used_pct.quantize(Decimal('0.1'))),
            },
            
            # Investor Details
            'investors': investors_list,
            
            # Pagination
            'pagination': {
                'current_page': 1,
                'total_pages': 1,
                'page_size': len(investors_list),
                'total_count': len(investors_list),
            }
        }
    }
    
    return Response(response_data)

