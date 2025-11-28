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


def _safe_decimal(value):
    """Safely convert value to Decimal"""
    if value is None:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except:
        return Decimal('0')


def _decimal_to_float(value):
    """Convert Decimal to float"""
    if value is None:
        return 0.0
    return float(value)


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
