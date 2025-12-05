"""
Investor Detail Views - Detailed information about individual investors
Including investment history, portfolio details, KYC status, and profile information
"""

from decimal import Decimal, ROUND_HALF_UP
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone

from investors.models import InvestorProfile
from investors.dashboard_models import Investment, KYCStatus
from spv.models import SPV
from users.models import TeamMember, CustomUser
from documents.models import Document
from django.db.models import Sum, Count
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def investor_detail(request, investor_id):
    """
    Get detailed information about a specific investor
    GET /api/investors/{investor_id}/
    
    Returns comprehensive investor information including:
    - Basic profile details
    - Investment metrics (amount, value, ownership, returns)
    - KYC/Accreditation status
    - Investment history
    - Residential and payment details
    """
    investor_profile = get_object_or_404(InvestorProfile, id=investor_id)
    user = investor_profile.user
    
    # Check permissions - user can view their own or admins can view all
    if not (request.user.id == user.id or request.user.is_staff or request.user.role == 'admin'):
        return Response({
            'error': 'You do not have permission to access this investor profile'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Calculate investment metrics (sample data - adjust based on actual investments)
    total_investment = Decimal('50000')  # Mock value - fetch from actual investments
    current_value = Decimal('57500')
    ownership_percent = Decimal('3')
    return_percent = Decimal('15')
    
    response_data = {
        'success': True,
        'data': {
            'investor_id': investor_profile.id,
            'user_id': user.id,
            
            # Header Section
            'header': {
                'full_name': investor_profile.full_name or user.get_full_name() or user.username,
                'email': investor_profile.email_address or user.email,
                'phone': investor_profile.phone_number,
                'kyc_status': investor_profile.application_status,
                'kyc_status_label': investor_profile.get_application_status_display(),
                'is_accredited': investor_profile.is_accredited_investor,
            },
            
            # Investment Metrics
            'investment_metrics': {
                'investment_amount': _decimal_to_float(total_investment),
                'current_value': _decimal_to_float(current_value),
                'ownership_percentage': float(ownership_percent),
                'return_percentage': float(return_percent),
                'currency': 'USD',
            },
            
            # Investor Profile
            'profile': {
                'full_name': investor_profile.full_name or user.get_full_name(),
                'nationality': investor_profile.country_of_residence,
                'email_address': investor_profile.email_address or user.email,
                'kyc_status': investor_profile.application_status,
                'kyc_status_label': investor_profile.get_application_status_display(),
                'kyc_approved': investor_profile.application_status == 'approved',
            },
            
            # Contact Information
            'contact_info': {
                'phone_number': investor_profile.phone_number,
                'email': investor_profile.email_address or user.email,
                'country': investor_profile.country_of_residence,
            },
            
            # KYC & Accreditation
            'kyc_accreditation': {
                'full_legal_name': investor_profile.full_legal_name,
                'legal_place_of_residence': investor_profile.legal_place_of_residence,
                'date_of_birth': investor_profile.date_of_birth.isoformat() if investor_profile.date_of_birth else None,
                'investor_type': investor_profile.investor_type,
                'investor_type_label': investor_profile.get_investor_type_display() if investor_profile.investor_type else None,
                'is_accredited_investor': investor_profile.is_accredited_investor,
                'accreditation_method': investor_profile.accreditation_method,
                'meets_local_thresholds': investor_profile.meets_local_investment_thresholds,
                'application_status': investor_profile.application_status,
                'application_submitted': investor_profile.application_submitted,
                'submitted_at': investor_profile.submitted_at.isoformat() if investor_profile.submitted_at else None,
            },
            
            # Residential Address
            'residential_address': {
                'street_address': investor_profile.street_address,
                'city': investor_profile.city,
                'state_province': investor_profile.state_province,
                'zip_postal_code': investor_profile.zip_postal_code,
                'country': investor_profile.country,
            },
            
            # Payment/Bank Details
            'payment_details': {
                'bank_name': investor_profile.bank_name,
                'account_holder_name': investor_profile.account_holder_name,
                'account_number': investor_profile.bank_account_number[:4] + '****' if investor_profile.bank_account_number else None,  # Masked
                'swift_ifsc_code': investor_profile.swift_ifsc_code,
                'proof_of_ownership_submitted': investor_profile.proof_of_bank_ownership is not None,
            },
            
            # Documents
            'documents': {
                'government_id_submitted': investor_profile.government_id is not None,
                'proof_of_income_submitted': investor_profile.proof_of_income_net_worth is not None,
                'proof_of_bank_ownership_submitted': investor_profile.proof_of_bank_ownership is not None,
            },
            
            # Agreements Status
            'agreements': {
                'terms_and_conditions_accepted': investor_profile.terms_and_conditions_accepted,
                'risk_disclosure_accepted': investor_profile.risk_disclosure_accepted,
                'privacy_policy_accepted': investor_profile.privacy_policy_accepted,
                'confirmation_accepted': investor_profile.confirmation_of_true_information,
                'all_accepted': all([
                    investor_profile.terms_and_conditions_accepted,
                    investor_profile.risk_disclosure_accepted,
                    investor_profile.privacy_policy_accepted,
                    investor_profile.confirmation_of_true_information,
                ]),
            },
            
            # Risk Profile
            'risk_profile': {
                'investor_type': investor_profile.investor_type,
                'investor_type_label': investor_profile.get_investor_type_display() if investor_profile.investor_type else None,
                'is_accredited': investor_profile.is_accredited_investor,
            },
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def investor_investments(request, investor_id):
    """
    Get investment history and portfolio for an investor
    GET /api/investors/{investor_id}/investments/
    
    Returns:
    - List of SPVs investor is part of
    - Investment amounts per SPV
    - Current valuations
    - Returns and performance
    """
    investor_profile = get_object_or_404(InvestorProfile, id=investor_id)
    user = investor_profile.user
    
    # Check permissions
    if not (request.user.id == user.id or request.user.is_staff or request.user.role == 'admin'):
        return Response({
            'error': 'You do not have permission to access this investor profile'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Mock investment data - in real implementation, fetch from investor's actual investments
    investments = [
        {
            'spv_id': 1,
            'spv_name': 'Tech Startup Fund Q4 2024',
            'investment_amount': 50000,
            'current_value': 57500,
            'ownership_percentage': 3,
            'return_percentage': 15,
            'investment_date': '2024-09-28',
            'status': 'active',
            'portfolio_company': 'TechStartup Inc',
            'round': 'Series A',
            'stage': 'Series A',
        },
        {
            'spv_id': 2,
            'spv_name': 'Real Estate Opportunity',
            'investment_amount': 50000,
            'current_value': 50000,
            'ownership_percentage': 25,
            'return_percentage': 0,
            'investment_date': '2024-02-15',
            'status': 'active',
            'portfolio_company': 'Real Estate Inc',
            'round': 'Series B',
            'stage': 'Growth',
        },
        {
            'spv_id': 3,
            'spv_name': 'Healthcare Innovation',
            'investment_amount': 50000,
            'current_value': 50000,
            'ownership_percentage': 25,
            'return_percentage': 0,
            'investment_date': '2024-11-20',
            'status': 'active',
            'portfolio_company': 'HealthTech Inc',
            'round': 'Seed',
            'stage': 'Early Stage',
        }
    ]
    
    # Calculate totals
    total_invested = sum(inv['investment_amount'] for inv in investments)
    total_current_value = sum(inv['current_value'] for inv in investments)
    average_return = sum(inv['return_percentage'] for inv in investments) / len(investments) if investments else 0
    
    response_data = {
        'success': True,
        'data': {
            'investor_id': investor_profile.id,
            'investor_name': investor_profile.full_name or user.get_full_name(),
            'portfolio_summary': {
                'total_invested': total_invested,
                'total_current_value': total_current_value,
                'total_return': total_current_value - total_invested,
                'total_return_percentage': ((total_current_value - total_invested) / total_invested * 100) if total_invested > 0 else 0,
                'number_of_investments': len(investments),
                'average_return_percentage': average_return,
            },
            'investments': investments,
            'pagination': {
                'current_page': 1,
                'total_pages': 1,
                'page_size': 10,
                'total_count': len(investments)
            }
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def investor_kyc_status(request, investor_id):
    """
    Get detailed KYC/Accreditation status for an investor
    GET /api/investors/{investor_id}/kyc-status/
    
    Returns:
    - Application status
    - All agreements acceptance status
    - Document submission status
    - Accreditation details
    - Approval timeline
    """
    investor_profile = get_object_or_404(InvestorProfile, id=investor_id)
    user = investor_profile.user
    
    # Check permissions
    if not (request.user.id == user.id or request.user.is_staff or request.user.role == 'admin'):
        return Response({
            'error': 'You do not have permission to access this investor profile'
        }, status=status.HTTP_403_FORBIDDEN)
    
    response_data = {
        'success': True,
        'data': {
            'investor_id': investor_profile.id,
            'investor_name': investor_profile.full_name or user.get_full_name(),
            
            'application_status': {
                'current_status': investor_profile.application_status,
                'status_label': investor_profile.get_application_status_display(),
                'submitted': investor_profile.application_submitted,
                'submitted_at': investor_profile.submitted_at.isoformat() if investor_profile.submitted_at else None,
                'is_approved': investor_profile.application_status == 'approved',
            },
            
            'accreditation': {
                'is_accredited_investor': investor_profile.is_accredited_investor,
                'investor_type': investor_profile.investor_type,
                'investor_type_label': investor_profile.get_investor_type_display() if investor_profile.investor_type else None,
                'accreditation_method': investor_profile.accreditation_method,
                'accreditation_method_label': investor_profile.get_accreditation_method_display() if investor_profile.accreditation_method else None,
                'meets_local_thresholds': investor_profile.meets_local_investment_thresholds,
            },
            
            'agreements': {
                'terms_and_conditions': {
                    'accepted': investor_profile.terms_and_conditions_accepted,
                    'label': 'Terms & Conditions'
                },
                'risk_disclosure': {
                    'accepted': investor_profile.risk_disclosure_accepted,
                    'label': 'Risk Disclosure'
                },
                'privacy_policy': {
                    'accepted': investor_profile.privacy_policy_accepted,
                    'label': 'Privacy Policy'
                },
                'confirmation_of_information': {
                    'accepted': investor_profile.confirmation_of_true_information,
                    'label': 'Confirmation of True Information'
                },
                'all_agreements_accepted': all([
                    investor_profile.terms_and_conditions_accepted,
                    investor_profile.risk_disclosure_accepted,
                    investor_profile.privacy_policy_accepted,
                    investor_profile.confirmation_of_true_information,
                ]),
            },
            
            'documents': {
                'government_id': {
                    'submitted': investor_profile.government_id is not None,
                    'label': 'Government-Issued ID'
                },
                'proof_of_income_net_worth': {
                    'submitted': investor_profile.proof_of_income_net_worth is not None,
                    'label': 'Proof of Income/Net Worth'
                },
                'proof_of_bank_ownership': {
                    'submitted': investor_profile.proof_of_bank_ownership is not None,
                    'label': 'Proof of Bank Ownership'
                },
                'all_documents_submitted': all([
                    investor_profile.government_id is not None,
                    investor_profile.proof_of_income_net_worth is not None,
                    investor_profile.proof_of_bank_ownership is not None,
                ]),
            },
            
            'completion_checklist': [
                {
                    'step': 1,
                    'title': 'Basic Information',
                    'completed': bool(investor_profile.full_name and investor_profile.email_address),
                    'items': [
                        {'label': 'Full Name', 'completed': bool(investor_profile.full_name)},
                        {'label': 'Email', 'completed': bool(investor_profile.email_address)},
                        {'label': 'Phone', 'completed': bool(investor_profile.phone_number)},
                    ]
                },
                {
                    'step': 2,
                    'title': 'KYC / Identity Verification',
                    'completed': bool(investor_profile.government_id and investor_profile.date_of_birth),
                    'items': [
                        {'label': 'Government ID', 'completed': bool(investor_profile.government_id)},
                        {'label': 'Date of Birth', 'completed': bool(investor_profile.date_of_birth)},
                    ]
                },
                {
                    'step': 3,
                    'title': 'Bank Details',
                    'completed': bool(investor_profile.bank_account_number and investor_profile.bank_name),
                    'items': [
                        {'label': 'Bank Name', 'completed': bool(investor_profile.bank_name)},
                        {'label': 'Account Details', 'completed': bool(investor_profile.bank_account_number)},
                    ]
                },
                {
                    'step': 4,
                    'title': 'Accreditation',
                    'completed': investor_profile.is_accredited_investor,
                    'items': [
                        {'label': 'Accreditation Verified', 'completed': investor_profile.is_accredited_investor},
                        {'label': 'Proof Submitted', 'completed': bool(investor_profile.proof_of_income_net_worth)},
                    ]
                },
                {
                    'step': 5,
                    'title': 'Agreements',
                    'completed': all([
                        investor_profile.terms_and_conditions_accepted,
                        investor_profile.risk_disclosure_accepted,
                        investor_profile.privacy_policy_accepted,
                    ]),
                    'items': [
                        {'label': 'Terms & Conditions', 'completed': investor_profile.terms_and_conditions_accepted},
                        {'label': 'Risk Disclosure', 'completed': investor_profile.risk_disclosure_accepted},
                        {'label': 'Privacy Policy', 'completed': investor_profile.privacy_policy_accepted},
                    ]
                },
            ],
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def investor_risk_profile(request, investor_id):
    """
    Get investor's risk profile and preferences
    GET /api/investors/{investor_id}/risk-profile/
    
    Returns:
    - Investor type
    - Accreditation status
    - Investment preferences
    - Risk tolerance
    - Experience level
    """
    investor_profile = get_object_or_404(InvestorProfile, id=investor_id)
    user = investor_profile.user
    
    # Check permissions
    if not (request.user.id == user.id or request.user.is_staff or request.user.role == 'admin'):
        return Response({
            'error': 'You do not have permission to access this investor profile'
        }, status=status.HTTP_403_FORBIDDEN)
    
    response_data = {
        'success': True,
        'data': {
            'investor_id': investor_profile.id,
            'investor_name': investor_profile.full_name or user.get_full_name(),
            
            'risk_profile': {
                'investor_type': investor_profile.investor_type,
                'investor_type_label': investor_profile.get_investor_type_display() if investor_profile.investor_type else None,
                'is_accredited': investor_profile.is_accredited_investor,
                'accreditation_status': investor_profile.get_accreditation_method_display() if investor_profile.accreditation_method else 'Not Accredited',
            },
            
            'investment_details': {
                'full_legal_name': investor_profile.full_legal_name,
                'legal_place_of_residence': investor_profile.legal_place_of_residence,
                'country_of_residence': investor_profile.country_of_residence,
                'meets_local_thresholds': investor_profile.meets_local_investment_thresholds,
            },
            
            'compliance': {
                'terms_accepted': investor_profile.terms_and_conditions_accepted,
                'risk_acknowledged': investor_profile.risk_disclosure_accepted,
                'privacy_agreed': investor_profile.privacy_policy_accepted,
                'information_verified': investor_profile.confirmation_of_true_information,
                'all_compliance_complete': all([
                    investor_profile.terms_and_conditions_accepted,
                    investor_profile.risk_disclosure_accepted,
                    investor_profile.privacy_policy_accepted,
                    investor_profile.confirmation_of_true_information,
                ]),
            },
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_investment_detail(request, spv_id):
    """
    Get complete SPV details for investment page
    Includes investment overview, funding progress, details, and stats
    Used when investor clicks on a deal from Discover Deals page
    
    GET /api/investors/spv/{spv_id}/investment-detail/
    """
    spv = get_object_or_404(SPV, id=spv_id)
    user = request.user
    
    # Calculate funding progress
    total_investments = Investment.objects.filter(spv=spv)
    active_investments = total_investments.filter(status__in=['active', 'pending'])
    
    raised_amount = active_investments.aggregate(Sum('invested_amount'))['invested_amount__sum'] or 0
    target_amount = spv.round_size or spv.allocation or 0
    
    funding_percentage = 0
    if target_amount > 0:
        funding_percentage = min(100, (float(raised_amount) / float(target_amount)) * 100)
    
    # Calculate days left
    days_left = 22  # Default
    if spv.target_closing_date:
        delta = spv.target_closing_date - timezone.now().date()
        days_left = max(0, delta.days)
    
    # Count total investors
    total_investors = total_investments.values('investor').distinct().count()
    
    # Check if current user has already invested
    user_investment = Investment.objects.filter(investor=user, spv=spv).first()
    already_invested = user_investment is not None
    user_invested_amount = float(user_investment.invested_amount) if user_investment else 0
    
    # Determine risk level based on company stage or other factors
    risk_level = 'Medium'  # Default
    if spv.company_stage:
        stage_name = str(spv.company_stage).lower()
        if 'seed' in stage_name or 'pre-seed' in stage_name:
            risk_level = 'High'
        elif 'series a' in stage_name or 'series b' in stage_name:
            risk_level = 'Medium'
        elif 'series c' in stage_name or 'series d' in stage_name or 'late' in stage_name:
            risk_level = 'Low'
    
    # Prepare response data matching the UI design
    response_data = {
        'success': True,
        'spv_id': spv.id,
        
        # Investment Overview Section
        'overview': {
            'company_name': spv.portfolio_company_name or spv.display_name,
            'display_name': spv.display_name,
            'company_type': spv.portfolio_company.description if spv.portfolio_company else 'Enterprise Software',
            'description': spv.deal_memo or f"Leading AI-powered enterprise software company revolutionizing business automation",
            'stage': str(spv.company_stage) if spv.company_stage else 'Series B',
            'valuation': f"${float(spv.round_size) / 1000000:.0f}M" if spv.round_size else 'N/A',
            'expected_returns': '3-5x',  # Can be calculated or stored
            'timeline': '5-7 Years',  # Standard timeline
        },
        
        # Funding Progress
        'funding': {
            'raised': float(raised_amount),
            'raised_formatted': f"${float(raised_amount) / 1000000:.1f}M",
            'target': float(target_amount),
            'target_formatted': f"${float(target_amount) / 1000000:.0f}M",
            'percentage': round(funding_percentage, 0),
        },
        
        # Investment Details (Right sidebar)
        'details': {
            'status': spv.status,
            'status_label': 'Active' if spv.status in ['active', 'approved'] else spv.get_status_display(),
            'risk_level': risk_level,
            'min_investment': float(spv.minimum_lp_investment) if spv.minimum_lp_investment else 25000,
            'max_investment': float(spv.allocation) if spv.allocation else 500000,
            'lead_investor': f"{spv.created_by.first_name} {spv.created_by.last_name}".strip() or spv.created_by.username if spv.created_by else 'Unknown',
            'days_left': days_left,
            'target_closing_date': str(spv.target_closing_date) if spv.target_closing_date else None,
        },
        
        # Company Details (Tabs content)
        'company_details': {
            'business_model': 'SaaS platform with enterprise clients, recurring revenue model with 95% retention rate.',
            'market_opportunity': '$50B+ addressable market in enterprise automation, growing at 25% CAGR.',
            'competitive_advantage': 'Proprietary AI technology with 3+ years R&D lead over competitors.',
            'deal_memo': spv.deal_memo,
        },
        
        # Documents
        'documents': {
            'pitch_deck': spv.pitch_deck.url if spv.pitch_deck else None,
            'supporting_document': spv.supporting_document.url if spv.supporting_document else None,
        },
        
        # Investment Stats
        'stats': {
            'total_investors': total_investors,
            'days_remaining': days_left,
            'expected_returns': '3-5x',
        },
        
        # User's investment status
        'user_status': {
            'already_invested': already_invested,
            'invested_amount': user_invested_amount,
            'investment_status': user_investment.status if user_investment else None,
        },
        
        # Additional Info
        'additional_info': {
            'transaction_type': spv.get_transaction_type_display() if spv.transaction_type else None,
            'instrument_type': str(spv.instrument_type) if spv.instrument_type else None,
            'share_class': str(spv.share_class) if spv.share_class else None,
            'round': str(spv.round) if spv.round else None,
            'valuation_type': spv.get_valuation_type_display() if spv.valuation_type else None,
            'total_carry_percentage': float(spv.total_carry_percentage) if spv.total_carry_percentage else 0,
            'deal_tags': spv.deal_tags or [],
            'jurisdiction': spv.jurisdiction,
            'access_mode': spv.get_access_mode_display() if spv.access_mode else 'Private',
        },
        
        # Contact
        'contact': {
            'founder_email': spv.founder_email,
            'lead_name': f"{spv.created_by.first_name} {spv.created_by.last_name}".strip() or spv.created_by.username if spv.created_by else 'Unknown',
            'lead_email': spv.created_by.email if spv.created_by else None,
        },
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_financials(request, spv_id):
    """
    Get SPV financial data for Financials tab
    Includes Key KPIs and Financial Summary table
    
    GET /api/investors/spv/{spv_id}/financials/
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Calculate Key KPIs
    # These would typically come from a financial model/data
    # For now, using placeholder calculations
    
    arr = 0  # Annual Recurring Revenue
    mrr = 0   # Monthly Recurring Revenue
    gross_margin = 0  # Percentage
    monthly_burn = 0  # Monthly burn rate
    
    # Financial Summary - Yearly data
    # This should come from a FinancialData model linked to SPV
    # For now, providing sample data structure
    financial_summary = [
        {
            'year': 0000,
            'revenue': 0,
            'revenue_formatted': '$0',
            'ebitda': 0,
            'ebitda_formatted': '$0',
            'cash': 0,
            'cash_formatted': '$0M',
        },
        {
            'year': 0,
            'revenue': 0,
            'revenue_formatted': '$0M',
            'ebitda': 0,
            'ebitda_formatted': '$0M',
            'cash': 0,
            'cash_formatted': '$0M',
        },
        {
            'year': 0000,
            'revenue': 0,
            'revenue_formatted': '$0M',
            'ebitda': 0,
            'ebitda_formatted': '$0M',
            'cash': 0,
            'cash_formatted': '$0M',
        },
        {
            'year': 0000,
            'revenue': 0,
            'revenue_formatted': '$0M',
            'ebitda': 0,
            'ebitda_formatted': '$0M',
            'cash': 0,
            'cash_formatted': '$0M',
        },
    ]
    
    response_data = {
        'success': True,
        'spv_id': spv.id,
        'spv_name': spv.display_name,
        
        # Key KPIs
        'key_kpis': {
            'arr': arr,
            'arr_formatted': f'${arr / 1000000:.1f}M',
            'mrr': mrr,
            'mrr_formatted': f'${mrr / 1000000:.2f}M',
            'gross_margin': gross_margin,
            'gross_margin_formatted': f'{gross_margin}%',
            'monthly_burn': monthly_burn,
            'monthly_burn_formatted': f'${monthly_burn:,}',
        },
        
        # Financial Summary Table
        'financial_summary': {
            'title': f'{spv.portfolio_company_name} Financial Summary',
            'subtitle': 'Yearly revenue, EBITDA, and cash balance',
            'data': financial_summary,
        },
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_team(request, spv_id):
    """
    Get SPV team members for Team tab
    Shows leadership team and core members
    
    GET /api/investors/spv/{spv_id}/team/
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Get team members associated with this SPV's syndicate
    team_members = []
    
    if spv.created_by and hasattr(spv.created_by, 'syndicate_profile'):
        syndicate = spv.created_by.syndicate_profile
        members = TeamMember.objects.filter(
            syndicate=syndicate,
            is_active=True
        ).select_related('user')
        
        for member in members:
            team_members.append({
                'id': member.id,
                'name': member.name,
                'email': member.email,
                'role': member.role,
                'role_display': member.get_role_display(),
                'title': member.get_role_display(),  # e.g., "CEO & Co-Founder"
                'description': f"{'Registered' if member.is_registered else 'Invited'} member",
                'avatar': None,  # Add avatar URL if available
                'linkedin': None,  # Add if you have LinkedIn field
                'is_registered': member.is_registered,
                'added_at': member.added_at.strftime('%d/%m/%Y'),
            })
    
    # If no team members found, create sample data for display
    if not team_members:
        team_members = [
            {
                'id': 1,
                'name': 'Alex Morgan',
                'email': spv.founder_email,
                'role': 'partner',
                'role_display': 'Partner',
                'title': 'CEO & Co-Founder',
                'description': 'Former product lead at top SaaS unicorn. 10+ years in enterprise AI.',
                'avatar': None,
                'linkedin': None,
                'is_registered': False,
            }
        ]
    
    response_data = {
        'success': True,
        'spv_id': spv.id,
        'spv_name': spv.display_name,
        
        # Leadership Team
        'team': {
            'title': 'Leadership Team',
            'subtitle': 'Core executives and functional leaders',
            'members': team_members,
            'total_members': len(team_members),
        },
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def spv_documents(request, spv_id):
    """
    Get SPV documents for Documents tab
    Shows investment documents available for download
    
    GET /api/investors/spv/{spv_id}/documents/
    """
    spv = get_object_or_404(SPV, id=spv_id)
    
    # Get documents associated with this SPV
    documents = Document.objects.filter(
        spv=spv,
        status__in=['signed', 'finalized', 'pending_signatures']
    ).order_by('-created_at')
    
    documents_list = []
    for doc in documents:
        documents_list.append({
            'id': doc.id,
            'document_id': doc.document_id,
            'title': doc.title,
            'description': doc.description or '',
            'document_type': doc.document_type,
            'document_type_display': doc.get_document_type_display(),
            'file_url': doc.file.url if doc.file else None,
            'file_name': doc.original_filename or doc.title,
            'file_size': doc.file_size,
            'file_size_mb': doc.file_size_mb,
            'file_size_formatted': f'{doc.file_size_mb} MB',
            'mime_type': doc.mime_type,
            'status': doc.status,
            'status_display': doc.get_status_display(),
            'version': doc.version,
            'created_at': doc.created_at.strftime('%d/%m/%Y'),
            'finalized_at': doc.finalized_at.strftime('%d/%m/%Y') if doc.finalized_at else None,
        })
    
    
    response_data = {
        'success': True,
        'spv_id': spv.id,
        'spv_name': spv.display_name,
        
        # Investment Documents
        'documents': {
            'title': 'Investment Documents',
            'subtitle': 'Review all relevant documents before investing',
            'items': documents_list,
            'total_documents': len(documents_list),
        },
    }
    
    return Response(response_data)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def investor_identity_settings(request):
    """
    Get or update investor identity and jurisdiction settings
    
    GET /api/investors/settings/identity/ - Get current identity information
    PUT /api/investors/settings/identity/ - Update identity information
    
    PUT/PATCH Payload:
    {
        "full_legal_name": "John Michael Smith",
        "country_of_residence": "United States",
        "tax_domicile": "United States",
        "national_id_passport": "123-45-6789",
        "date_of_birth": "1985-06-15",
        "street_address": "123 Main St",
        "city": "New York",
        "state_province": "NY",
        "zip_postal_code": "10001",
        "country": "United States"
    }
    """
    user = request.user
    
    # Get or create investor profile
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Format date of birth
        dob_formatted = None
        if investor_profile.date_of_birth:
            dob_formatted = investor_profile.date_of_birth.strftime('%d-%m-%Y')
        
        # Format full address
        full_address = None
        if investor_profile.street_address:
            address_parts = [
                investor_profile.street_address,
                investor_profile.city,
                investor_profile.state_province,
                investor_profile.zip_postal_code
            ]
            full_address = ', '.join([part for part in address_parts if part])
        
        # Determine jurisdiction status (can be enhanced with actual logic)
        jurisdiction_status = 'approved'  # Default, can be calculated based on verification
        
        response_data = {
            'success': True,
            'identity': {
                'full_legal_name': investor_profile.full_legal_name or investor_profile.full_name or '',
                'country_of_residence': investor_profile.country_of_residence or '',
                'tax_domicile': investor_profile.country_of_residence or '',  # Using same as residence for now
                'national_id': investor_profile.national_id or '',
                'date_of_birth': dob_formatted or '',
                'date_of_birth_raw': str(investor_profile.date_of_birth) if investor_profile.date_of_birth else None,
                'full_address': full_address or '',
                'street_address': investor_profile.street_address or '',
                'city': investor_profile.city or '',
                'state_province': investor_profile.state_province or '',
                'zip_postal_code': investor_profile.zip_postal_code or '',
                'country': investor_profile.country or investor_profile.country_of_residence or '',
            },
            'jurisdiction': {
                'status': jurisdiction_status,
                'status_label': 'Approved',
                'message': 'Auto-tagged based on residence',
            },
            'government_id_uploaded': bool(investor_profile.government_id),
            'government_id_url': investor_profile.government_id.url if investor_profile.government_id else None,
        }
        
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Update identity information
        data = request.data
        
        # Update fields if provided
        if 'full_legal_name' in data:
            investor_profile.full_legal_name = data['full_legal_name']
            # Also update full_name if it's empty
            if not investor_profile.full_name:
                investor_profile.full_name = data['full_legal_name']
        
        if 'country_of_residence' in data:
            investor_profile.country_of_residence = data['country_of_residence']
        
        if 'date_of_birth' in data:
            try:
                # Handle different date formats
                dob_str = data['date_of_birth']
                if isinstance(dob_str, str):
                    # Try different formats
                    from datetime import datetime
                    for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            investor_profile.date_of_birth = datetime.strptime(dob_str, fmt).date()
                            break
                        except ValueError:
                            continue
                    else:
                        return Response({
                            'error': 'Invalid date format. Use YYYY-MM-DD, DD-MM-YYYY, or MM/DD/YYYY'
                        }, status=status.HTTP_400_BAD_REQUEST)
                else:
                    investor_profile.date_of_birth = dob_str
            except Exception as e:
                return Response({
                    'error': f'Invalid date of birth: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update address fields
        if 'street_address' in data:
            investor_profile.street_address = data['street_address']
        if 'city' in data:
            investor_profile.city = data['city']
        if 'state_province' in data:
            investor_profile.state_province = data['state_province']
        if 'zip_postal_code' in data:
            investor_profile.zip_postal_code = data['zip_postal_code']
        if 'country' in data:
            investor_profile.country = data['country']
        
        # Tax domicile (using country_of_residence for now, can add separate field later)
        if 'tax_domicile' in data:
            # If tax_domicile is different, we might want to store it separately
            # For now, we'll use country_of_residence
            if not investor_profile.country_of_residence:
                investor_profile.country_of_residence = data['tax_domicile']
        
        # National ID/Passport
        if 'national_id' in data:
            investor_profile.national_id = data['national_id']
        
        investor_profile.save()
        
        # Format response
        dob_formatted = None
        if investor_profile.date_of_birth:
            dob_formatted = investor_profile.date_of_birth.strftime('%d-%m-%Y')
        
        full_address = None
        if investor_profile.street_address:
            address_parts = [
                investor_profile.street_address,
                investor_profile.city,
                investor_profile.state_province,
                investor_profile.zip_postal_code
            ]
            full_address = ', '.join([part for part in address_parts if part])
        
        response_data = {
            'success': True,
            'message': 'Identity information updated successfully',
            'identity': {
                'full_legal_name': investor_profile.full_legal_name or investor_profile.full_name or '',
                'country_of_residence': investor_profile.country_of_residence or '',
                'tax_domicile': investor_profile.country_of_residence or '',
                'national_id': investor_profile.national_id or '',
                'date_of_birth': dob_formatted or '',
                'date_of_birth_raw': str(investor_profile.date_of_birth) if investor_profile.date_of_birth else None,
                'full_address': full_address or '',
                'street_address': investor_profile.street_address or '',
                'city': investor_profile.city or '',
                'state_province': investor_profile.state_province or '',
                'zip_postal_code': investor_profile.zip_postal_code or '',
                'country': investor_profile.country or investor_profile.country_of_residence or '',
            },
            'jurisdiction': {
                'status': 'approved',
                'status_label': 'Approved',
                'message': 'Auto-tagged based on residence',
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def investor_accreditation_settings(request):
    """
    Get or update investor accreditation settings
    
    GET /api/investors/settings/accreditation/ - Get current accreditation information
    PUT /api/investors/settings/accreditation/ - Update accreditation information
    
    PUT/PATCH Payload:
    {
        "accreditation_type": "U.S.: Reg D Rule 501(a)",
        "accreditation_method": "series_7_65_82",
        "accreditation_expiry_date": "2025-12-31",
        "is_accredited_investor": true,
        "meets_local_investment_thresholds": true
    }
    """
    user = request.user
    
    # Get or create investor profile
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Map accreditation method to accreditation type
        accreditation_type_map = {
            'at_least_5m': 'U.S.: Reg D Rule 501(a)',
            'between_2.2m_5m': 'U.S.: Reg D Rule 501(a)',
            'between_1m_2.2m': 'U.S.: Reg D Rule 501(a)',
            'income_200k': 'U.S.: Reg D Rule 501(a)',
            'series_7_65_82': 'U.S.: Reg D Rule 501(a)',
            'not_accredited': 'Not Accredited',
        }
        
        accreditation_type = accreditation_type_map.get(
            investor_profile.accreditation_method, 
            'U.S.: Reg D Rule 501(a)' if investor_profile.is_accredited_investor else 'Not Accredited'
        )
        
        # Determine verification status
        verification_status = 'verified' if investor_profile.is_accredited_investor else 'pending'
        if investor_profile.application_status == 'approved':
            verification_status = 'verified'
        elif investor_profile.application_status == 'rejected':
            verification_status = 'rejected'
        
        # Check required documents
        income_statement_uploaded = bool(investor_profile.proof_of_income_net_worth)
        net_worth_statement_uploaded = bool(investor_profile.proof_of_income_net_worth)
        professional_license_uploaded = investor_profile.accreditation_method == 'series_7_65_82'
        
        # Format expiry date from model field or default
        expiry_date = investor_profile.accreditation_expiry_date
        expiry_date_formatted = None
        if expiry_date:
            expiry_date_formatted = expiry_date.strftime('%m/%d/%Y')
        elif investor_profile.is_accredited_investor:
            # Default to 1 year from submission or current date if not set
            from datetime import timedelta
            if investor_profile.submitted_at:
                expiry_date = (investor_profile.submitted_at + timedelta(days=365)).date()
            else:
                expiry_date = (timezone.now() + timedelta(days=365)).date()
            expiry_date_formatted = expiry_date.strftime('%m/%d/%Y')
        
        response_data = {
            'success': True,
            'accreditation': {
                'accreditation_type': accreditation_type,
                'accreditation_method': investor_profile.accreditation_method or '',
                'accreditation_method_display': investor_profile.get_accreditation_method_display() if investor_profile.accreditation_method else '',
                'accreditation_expiry_date': expiry_date_formatted,
                'accreditation_expiry_date_raw': str(expiry_date) if expiry_date else None,
                'is_accredited_investor': investor_profile.is_accredited_investor,
                'meets_local_investment_thresholds': investor_profile.meets_local_investment_thresholds,
            },
            'verification': {
                'status': verification_status,
                'status_label': 'Verified' if verification_status == 'verified' else 'Pending',
                'message': 'Current accreditation verification',
            },
            'required_documents': {
                'income_statement': {
                    'name': 'Income Statement',
                    'uploaded': income_statement_uploaded,
                    'status': 'Uploaded' if income_statement_uploaded else 'Not Uploaded',
                    'file_url': investor_profile.proof_of_income_net_worth.url if investor_profile.proof_of_income_net_worth else None,
                },
                'net_worth_statement': {
                    'name': 'Net Worth Statement',
                    'uploaded': net_worth_statement_uploaded,
                    'status': 'Uploaded' if net_worth_statement_uploaded else 'Not Uploaded',
                    'file_url': investor_profile.proof_of_income_net_worth.url if investor_profile.proof_of_income_net_worth else None,
                },
                'professional_license': {
                    'name': 'Professional License',
                    'uploaded': professional_license_uploaded,
                    'status': 'Uploaded' if professional_license_uploaded else 'Not Uploaded',
                    'file_url': None,  # Can be enhanced if license is stored separately
                },
            },
        }
        
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Update accreditation information
        data = request.data
        
        # Update accreditation method/type
        if 'accreditation_method' in data:
            investor_profile.accreditation_method = data['accreditation_method']
        elif 'accreditation_type' in data:
            # Map accreditation type back to method if needed
            # For now, if type is provided, we'll keep existing method or set default
            pass
        
        if 'is_accredited_investor' in data:
            investor_profile.is_accredited_investor = bool(data['is_accredited_investor'])
        
        if 'meets_local_investment_thresholds' in data:
            investor_profile.meets_local_investment_thresholds = bool(data['meets_local_investment_thresholds'])
        
        # Handle expiry date
        if 'accreditation_expiry_date' in data:
            expiry_date_str = data['accreditation_expiry_date']
            try:
                from datetime import datetime
                for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%d/%m/%Y']:
                    try:
                        investor_profile.accreditation_expiry_date = datetime.strptime(expiry_date_str, fmt).date()
                        break
                    except ValueError:
                        continue
                else:
                    return Response({
                        'error': 'Invalid date format. Use YYYY-MM-DD, MM/DD/YYYY, or DD-MM-YYYY'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({
                    'error': f'Invalid accreditation expiry date: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        investor_profile.save()
        
        # Format response
        accreditation_type_map = {
            'at_least_5m': 'U.S.: Reg D Rule 501(a)',
            'between_2.2m_5m': 'U.S.: Reg D Rule 501(a)',
            'between_1m_2.2m': 'U.S.: Reg D Rule 501(a)',
            'income_200k': 'U.S.: Reg D Rule 501(a)',
            'series_7_65_82': 'U.S.: Reg D Rule 501(a)',
            'not_accredited': 'Not Accredited',
        }
        
        accreditation_type = accreditation_type_map.get(
            investor_profile.accreditation_method, 
            'U.S.: Reg D Rule 501(a)' if investor_profile.is_accredited_investor else 'Not Accredited'
        )
        
        verification_status = 'verified' if investor_profile.is_accredited_investor else 'pending'
        if investor_profile.application_status == 'approved':
            verification_status = 'verified'
        
        income_statement_uploaded = bool(investor_profile.proof_of_income_net_worth)
        net_worth_statement_uploaded = bool(investor_profile.proof_of_income_net_worth)
        professional_license_uploaded = investor_profile.accreditation_method == 'series_7_65_82'
        
        expiry_date = investor_profile.accreditation_expiry_date
        expiry_date_formatted = None
        if expiry_date:
            expiry_date_formatted = expiry_date.strftime('%m/%d/%Y')
        elif investor_profile.is_accredited_investor:
            from datetime import timedelta
            if investor_profile.submitted_at:
                expiry_date = (investor_profile.submitted_at + timedelta(days=365)).date()
            else:
                expiry_date = (timezone.now() + timedelta(days=365)).date()
            expiry_date_formatted = expiry_date.strftime('%m/%d/%Y')
        
        response_data = {
            'success': True,
            'message': 'Accreditation details updated successfully',
            'accreditation': {
                'accreditation_type': accreditation_type,
                'accreditation_method': investor_profile.accreditation_method or '',
                'accreditation_method_display': investor_profile.get_accreditation_method_display() if investor_profile.accreditation_method else '',
                'accreditation_expiry_date': expiry_date_formatted,
                'accreditation_expiry_date_raw': str(expiry_date) if expiry_date else None,
                'is_accredited_investor': investor_profile.is_accredited_investor,
                'meets_local_investment_thresholds': investor_profile.meets_local_investment_thresholds,
            },
            'verification': {
                'status': verification_status,
                'status_label': 'Verified' if verification_status == 'verified' else 'Pending',
                'message': 'Current accreditation verification',
            },
            'required_documents': {
                'income_statement': {
                    'name': 'Income Statement',
                    'uploaded': income_statement_uploaded,
                    'status': 'Uploaded' if income_statement_uploaded else 'Not Uploaded',
                },
                'net_worth_statement': {
                    'name': 'Net Worth Statement',
                    'uploaded': net_worth_statement_uploaded,
                    'status': 'Uploaded' if net_worth_statement_uploaded else 'Not Uploaded',
                },
                'professional_license': {
                    'name': 'Professional License',
                    'uploaded': professional_license_uploaded,
                    'status': 'Uploaded' if professional_license_uploaded else 'Not Uploaded',
                },
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def investor_tax_compliance_settings(request):
    """
    Get or update investor tax and compliance settings
    
    GET /api/investors/settings/tax-compliance/ - Get current tax and compliance information
    PUT /api/investors/settings/tax-compliance/ - Update tax and compliance information
    
    PUT/PATCH Payload:
    {
        "tax_identification_number": "123-45-6789",
        "us_person_status": true,
        "w9_form_submitted": true,
        "k1_acceptance": true,
        "tax_reporting_consent": true
    }
    """
    user = request.user
    
    # Get or create investor profile
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Get KYC status for AML/KYC status
    try:
        kyc_status = KYCStatus.objects.get(user=user)
        aml_kyc_status = kyc_status.status
    except KYCStatus.DoesNotExist:
        aml_kyc_status = 'not_started'
    
    if request.method == 'GET':
        # Get tax identification number from model field
        tax_id = investor_profile.tax_identification_number or ''
        
        # Get US Person Status from model field
        us_person_status = investor_profile.us_person_status
        
        # Get W-9 Form Submitted from model field
        w9_submitted = investor_profile.w9_form_submitted
        
        # Get K-1 Acceptance and Tax Reporting Consent from model fields
        k1_acceptance = investor_profile.k1_acceptance
        tax_reporting_consent = investor_profile.tax_reporting_consent
        
        # Map AML/KYC status
        aml_kyc_status_map = {
            'verified': 'passed',
            'approved': 'passed',
            'pending': 'pending',
            'in_review': 'pending',
            'rejected': 'failed',
            'not_started': 'pending',
        }
        aml_kyc_display = aml_kyc_status_map.get(aml_kyc_status, 'pending')
        
        response_data = {
            'success': True,
            'tax_compliance': {
                'tax_identification_number': tax_id,
                'us_person_status': us_person_status,
                'us_person_status_label': 'U.S. Person' if us_person_status else 'Non-U.S. Person',
                'w9_form_submitted': w9_submitted,
                'w9_form_submitted_label': 'Submitted' if w9_submitted else 'Not Submitted',
                'k1_acceptance': k1_acceptance,
                'k1_acceptance_label': 'Accepted' if k1_acceptance else 'Not Accepted',
                'tax_reporting_consent': tax_reporting_consent,
                'tax_reporting_consent_label': 'Consented' if tax_reporting_consent else 'Not Consented',
            },
            'aml_kyc': {
                'status': aml_kyc_display,
                'status_label': 'Passed' if aml_kyc_display == 'passed' else 'Pending' if aml_kyc_display == 'pending' else 'Failed',
                'message': 'Anti-money laundering verification',
            },
        }
        
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        # Update tax and compliance information
        data = request.data
        
        # Update tax identification number
        if 'tax_identification_number' in data:
            investor_profile.tax_identification_number = data['tax_identification_number']
        
        # Update US Person Status
        if 'us_person_status' in data:
            investor_profile.us_person_status = bool(data['us_person_status'])
        
        # Update W-9 Form Submitted
        if 'w9_form_submitted' in data:
            investor_profile.w9_form_submitted = bool(data['w9_form_submitted'])
        
        # Update K-1 Acceptance
        if 'k1_acceptance' in data:
            investor_profile.k1_acceptance = bool(data['k1_acceptance'])
        
        # Update Tax Reporting Consent
        if 'tax_reporting_consent' in data:
            investor_profile.tax_reporting_consent = bool(data['tax_reporting_consent'])
        
        investor_profile.save()
        
        # Get updated values
        tax_id = investor_profile.tax_identification_number or ''
        us_person_status = investor_profile.us_person_status
        w9_submitted = investor_profile.w9_form_submitted
        k1_acceptance = investor_profile.k1_acceptance
        tax_reporting_consent = investor_profile.tax_reporting_consent
        
        # Get updated KYC status
        try:
            kyc_status = KYCStatus.objects.get(user=user)
            aml_kyc_status = kyc_status.status
        except KYCStatus.DoesNotExist:
            aml_kyc_status = 'not_started'
        
        aml_kyc_status_map = {
            'verified': 'passed',
            'approved': 'passed',
            'pending': 'pending',
            'in_review': 'pending',
            'rejected': 'failed',
            'not_started': 'pending',
        }
        aml_kyc_display = aml_kyc_status_map.get(aml_kyc_status, 'pending')
        
        response_data = {
            'success': True,
            'message': 'Tax & Compliance settings updated successfully',
            'tax_compliance': {
                'tax_identification_number': tax_id,
                'us_person_status': us_person_status,
                'us_person_status_label': 'U.S. Person' if us_person_status else 'Non-U.S. Person',
                'w9_form_submitted': w9_submitted,
                'w9_form_submitted_label': 'Submitted' if w9_submitted else 'Not Submitted',
                'k1_acceptance': k1_acceptance,
                'k1_acceptance_label': 'Accepted' if k1_acceptance else 'Not Accepted',
                'tax_reporting_consent': tax_reporting_consent,
                'tax_reporting_consent_label': 'Consented' if tax_reporting_consent else 'Not Consented',
            },
            'aml_kyc': {
                'status': aml_kyc_display,
                'status_label': 'Passed' if aml_kyc_display == 'passed' else 'Pending' if aml_kyc_display == 'pending' else 'Failed',
                'message': 'Anti-money laundering verification',
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def investor_eligibility_settings(request):
    """
    Get or update investor eligibility settings
    
    GET /api/investors/settings/eligibility/ - Get current eligibility information
    PUT /api/investors/settings/eligibility/ - Update eligibility information
    
    PUT/PATCH Payload:
    {
        "delaware_spvs_allowed": true,
        "bvi_spvs_allowed": false,
        "auto_reroute_consent": true,
        "max_annual_commitment": 500000,
        "deal_stage_preferences": ["early_stage", "growth", "late_stage"]
    }
    """
    user = request.user
    
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        response_data = {
            'success': True,
            'eligibility': {
                'jurisdiction_preferences': {
                    'delaware_spvs': {
                        'allowed': investor_profile.delaware_spvs_allowed,
                        'description': 'Allow investment in Delaware entities',
                    },
                    'bvi_spvs': {
                        'allowed': investor_profile.bvi_spvs_allowed,
                        'description': 'Allow investment in British Virgin Islands entities',
                    },
                    'auto_reroute_consent': {
                        'enabled': investor_profile.auto_reroute_consent,
                        'description': 'Offer alternative jurisdiction if ineligible',
                    },
                },
                'max_annual_commitment': float(investor_profile.max_annual_commitment) if investor_profile.max_annual_commitment else None,
                'max_annual_commitment_formatted': f'${investor_profile.max_annual_commitment:,.0f}' if investor_profile.max_annual_commitment else None,
                'deal_stage_preferences': investor_profile.deal_stage_preferences or [],
            },
        }
        
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        data = request.data
        
        if 'delaware_spvs_allowed' in data:
            investor_profile.delaware_spvs_allowed = bool(data['delaware_spvs_allowed'])
        if 'bvi_spvs_allowed' in data:
            investor_profile.bvi_spvs_allowed = bool(data['bvi_spvs_allowed'])
        if 'auto_reroute_consent' in data:
            investor_profile.auto_reroute_consent = bool(data['auto_reroute_consent'])
        if 'max_annual_commitment' in data:
            investor_profile.max_annual_commitment = data['max_annual_commitment']
        if 'deal_stage_preferences' in data:
            investor_profile.deal_stage_preferences = data['deal_stage_preferences']
        
        investor_profile.save()
        
        response_data = {
            'success': True,
            'message': 'Eligibility rules updated successfully',
            'eligibility': {
                'jurisdiction_preferences': {
                    'delaware_spvs': {
                        'allowed': investor_profile.delaware_spvs_allowed,
                        'description': 'Allow investment in Delaware entities',
                    },
                    'bvi_spvs': {
                        'allowed': investor_profile.bvi_spvs_allowed,
                        'description': 'Allow investment in British Virgin Islands entities',
                    },
                    'auto_reroute_consent': {
                        'enabled': investor_profile.auto_reroute_consent,
                        'description': 'Offer alternative jurisdiction if ineligible',
                    },
                },
                'max_annual_commitment': float(investor_profile.max_annual_commitment) if investor_profile.max_annual_commitment else None,
                'max_annual_commitment_formatted': f'${investor_profile.max_annual_commitment:,.0f}' if investor_profile.max_annual_commitment else None,
                'deal_stage_preferences': investor_profile.deal_stage_preferences or [],
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def investor_financial_settings(request):
    """
    Get or update investor financial settings
    
    GET /api/investors/settings/financial/ - Get current financial information
    PUT /api/investors/settings/financial/ - Update financial information
    
    PUT/PATCH Payload:
    {
        "preferred_investment_currency": "USD",
        "escrow_partner_selection": "Silicon Valley Bank",
        "capital_call_notification_preferences": {
            "email": false,
            "sms": true,
            "in_app": false
        },
        "carry_fees_display_preference": "detailed_breakdown"
    }
    """
    user = request.user
    
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Count linked bank accounts (from bank details)
        linked_bank_accounts_count = 0
        if investor_profile.bank_account_number:
            linked_bank_accounts_count = 1  # Can be enhanced to count multiple accounts
        
        response_data = {
            'success': True,
            'financial': {
                'preferred_investment_currency': investor_profile.preferred_investment_currency,
                'preferred_investment_currency_display': investor_profile.get_preferred_investment_currency_display(),
                'currency_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.CURRENCY_CHOICES],
                'linked_bank_accounts': {
                    'count': linked_bank_accounts_count,
                    'description': 'For wires and distributions',
                },
                'escrow_partner_selection': investor_profile.escrow_partner_selection or '',
                'capital_call_notification_preferences': investor_profile.capital_call_notification_preferences or {
                    'email': False,
                    'sms': True,
                    'in_app': False,
                },
                'carry_fees_display_preference': investor_profile.carry_fees_display_preference,
                'carry_fees_display_preference_display': investor_profile.get_carry_fees_display_preference_display(),
                'carry_fees_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.CARRY_FEES_DISPLAY_CHOICES],
            },
        }
        
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        data = request.data
        
        # Validate preferred_investment_currency
        if 'preferred_investment_currency' in data:
            currency = data['preferred_investment_currency']
            valid_currencies = [choice[0] for choice in InvestorProfile.CURRENCY_CHOICES]
            if currency not in valid_currencies:
                return Response({
                    'error': f'Invalid currency. Must be one of: {", ".join(valid_currencies)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            investor_profile.preferred_investment_currency = currency
        
        # Validate escrow_partner_selection
        if 'escrow_partner_selection' in data:
            investor_profile.escrow_partner_selection = data['escrow_partner_selection']
        
        # Validate capital_call_notification_preferences
        if 'capital_call_notification_preferences' in data:
            prefs = data['capital_call_notification_preferences']
            if not isinstance(prefs, dict):
                return Response({
                    'error': 'capital_call_notification_preferences must be a dictionary with email, sms, and in_app keys'
                }, status=status.HTTP_400_BAD_REQUEST)
            # Ensure all keys exist
            default_prefs = {
                'email': prefs.get('email', False),
                'sms': prefs.get('sms', True),
                'in_app': prefs.get('in_app', False),
            }
            investor_profile.capital_call_notification_preferences = default_prefs
        
        # Validate carry_fees_display_preference
        if 'carry_fees_display_preference' in data:
            preference = data['carry_fees_display_preference']
            valid_preferences = [choice[0] for choice in InvestorProfile.CARRY_FEES_DISPLAY_CHOICES]
            if preference not in valid_preferences:
                return Response({
                    'error': f'Invalid carry/fees display preference. Must be one of: {", ".join(valid_preferences)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            investor_profile.carry_fees_display_preference = preference
        
        investor_profile.save()
        
        linked_bank_accounts_count = 0
        if investor_profile.bank_account_number:
            linked_bank_accounts_count = 1
        
        response_data = {
            'success': True,
            'message': 'Financial settings updated successfully',
            'financial': {
                'preferred_investment_currency': investor_profile.preferred_investment_currency,
                'preferred_investment_currency_display': investor_profile.get_preferred_investment_currency_display(),
                'currency_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.CURRENCY_CHOICES],
                'linked_bank_accounts': {
                    'count': linked_bank_accounts_count,
                    'description': 'For wires and distributions',
                },
                'escrow_partner_selection': investor_profile.escrow_partner_selection or '',
                'capital_call_notification_preferences': investor_profile.capital_call_notification_preferences or {
                    'email': False,
                    'sms': True,
                    'in_app': False,
                },
                'carry_fees_display_preference': investor_profile.carry_fees_display_preference,
                'carry_fees_display_preference_display': investor_profile.get_carry_fees_display_preference_display(),
                'carry_fees_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.CARRY_FEES_DISPLAY_CHOICES],
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def investor_portfolio_settings(request):
    """
    Get or update investor portfolio settings
    
    GET /api/investors/settings/portfolio/ - Get current portfolio settings
    PUT /api/investors/settings/portfolio/ - Update portfolio settings
    
    PUT/PATCH Payload:
    {
        "portfolio_view_settings": "deal_by_deal",
        "secondary_transfer_consent": true,
        "liquidity_preference": "long_term",
        "whitelist_secondary_trading": false
    }
    """
    user = request.user
    
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        response_data = {
            'success': True,
            'portfolio': {
                'portfolio_view_settings': investor_profile.portfolio_view_settings,
                'portfolio_view_settings_display': investor_profile.get_portfolio_view_settings_display(),
                'portfolio_view_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.PORTFOLIO_VIEW_CHOICES],
                'secondary_transfer_consent': {
                    'enabled': investor_profile.secondary_transfer_consent,
                    'description': 'Allow listing holdings for resale',
                },
                'liquidity_preference': investor_profile.liquidity_preference,
                'liquidity_preference_display': investor_profile.get_liquidity_preference_display(),
                'liquidity_preference_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.LIQUIDITY_PREFERENCE_CHOICES],
                'whitelist_secondary_trading': {
                    'enabled': investor_profile.whitelist_secondary_trading,
                    'description': 'Pre-approved counterparties',
                },
            },
        }
        
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        data = request.data
        
        # Validate portfolio_view_settings
        if 'portfolio_view_settings' in data:
            view_setting = data['portfolio_view_settings']
            valid_settings = [choice[0] for choice in InvestorProfile.PORTFOLIO_VIEW_CHOICES]
            if view_setting not in valid_settings:
                return Response({
                    'error': f'Invalid portfolio view setting. Must be one of: {", ".join(valid_settings)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            investor_profile.portfolio_view_settings = view_setting
        
        # Validate secondary_transfer_consent
        if 'secondary_transfer_consent' in data:
            investor_profile.secondary_transfer_consent = bool(data['secondary_transfer_consent'])
        
        # Validate liquidity_preference
        if 'liquidity_preference' in data:
            preference = data['liquidity_preference']
            valid_preferences = [choice[0] for choice in InvestorProfile.LIQUIDITY_PREFERENCE_CHOICES]
            if preference not in valid_preferences:
                return Response({
                    'error': f'Invalid liquidity preference. Must be one of: {", ".join(valid_preferences)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            investor_profile.liquidity_preference = preference
        
        # Validate whitelist_secondary_trading
        if 'whitelist_secondary_trading' in data:
            investor_profile.whitelist_secondary_trading = bool(data['whitelist_secondary_trading'])
        
        investor_profile.save()
        
        response_data = {
            'success': True,
            'message': 'Portfolio settings updated successfully',
            'portfolio': {
                'portfolio_view_settings': investor_profile.portfolio_view_settings,
                'portfolio_view_settings_display': investor_profile.get_portfolio_view_settings_display(),
                'portfolio_view_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.PORTFOLIO_VIEW_CHOICES],
                'secondary_transfer_consent': {
                    'enabled': investor_profile.secondary_transfer_consent,
                    'description': 'Allow listing holdings for resale',
                },
                'liquidity_preference': investor_profile.liquidity_preference,
                'liquidity_preference_display': investor_profile.get_liquidity_preference_display(),
                'liquidity_preference_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.LIQUIDITY_PREFERENCE_CHOICES],
                'whitelist_secondary_trading': {
                    'enabled': investor_profile.whitelist_secondary_trading,
                    'description': 'Pre-approved counterparties',
                },
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def investor_security_privacy_settings(request):
    """
    Get or update investor security and privacy settings
    
    GET /api/investors/settings/security-privacy/ - Get current security and privacy settings
    PUT /api/investors/settings/security-privacy/ - Update security and privacy settings
    
    PUT/PATCH Payload:
    {
        "two_factor_authentication_enabled": true,
        "session_timeout_minutes": 30,
        "soft_wall_deal_preview": true,
        "discovery_opt_in": false,
        "anonymity_preference": false
    }
    """
    user = request.user
    
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        response_data = {
            'success': True,
            'security': {
                'two_factor_authentication': {
                    'enabled': investor_profile.two_factor_authentication_enabled,
                    'description': 'Email, SMS, or authenticator app',
                    'status_message': '2FA Enabled. Two-factor authentication is active on your account.' if investor_profile.two_factor_authentication_enabled else '2FA Disabled',
                },
                'session_timeout_minutes': investor_profile.session_timeout_minutes,
                'session_timeout_display': investor_profile.get_session_timeout_minutes_display(),
                'session_timeout_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.SESSION_TIMEOUT_CHOICES],
                'device_management': {
                    'description': 'View and remove logged-in devices',
                },
            },
            'privacy': {
                'soft_wall_deal_preview': {
                    'enabled': investor_profile.soft_wall_deal_preview,
                    'description': 'Show teaser info before full KYC',
                },
                'discovery_opt_in': {
                    'enabled': investor_profile.discovery_opt_in,
                    'description': 'Allow syndicate leads outside network to invite you',
                },
                'anonymity_preference': {
                    'enabled': investor_profile.anonymity_preference,
                    'description': 'Hide name from other LPs in same SPV',
                },
            },
        }
        
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        data = request.data
        
        if 'two_factor_authentication_enabled' in data:
            investor_profile.two_factor_authentication_enabled = bool(data['two_factor_authentication_enabled'])
        # Validate session_timeout_minutes
        if 'session_timeout_minutes' in data:
            timeout = data['session_timeout_minutes']
            valid_timeouts = [choice[0] for choice in InvestorProfile.SESSION_TIMEOUT_CHOICES]
            if timeout not in valid_timeouts:
                return Response({
                    'error': f'Invalid session timeout. Must be one of: {", ".join(map(str, valid_timeouts))} minutes'
                }, status=status.HTTP_400_BAD_REQUEST)
            investor_profile.session_timeout_minutes = timeout
        if 'soft_wall_deal_preview' in data:
            investor_profile.soft_wall_deal_preview = bool(data['soft_wall_deal_preview'])
        if 'discovery_opt_in' in data:
            investor_profile.discovery_opt_in = bool(data['discovery_opt_in'])
        if 'anonymity_preference' in data:
            investor_profile.anonymity_preference = bool(data['anonymity_preference'])
        
        investor_profile.save()
        
        response_data = {
            'success': True,
            'message': 'Security & Privacy settings updated successfully',
            'security': {
                'two_factor_authentication': {
                    'enabled': investor_profile.two_factor_authentication_enabled,
                    'description': 'Email, SMS, or authenticator app',
                    'status_message': '2FA Enabled. Two-factor authentication is active on your account.' if investor_profile.two_factor_authentication_enabled else '2FA Disabled',
                },
                'session_timeout_minutes': investor_profile.session_timeout_minutes,
                'session_timeout_display': investor_profile.get_session_timeout_minutes_display(),
                'session_timeout_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.SESSION_TIMEOUT_CHOICES],
                'device_management': {
                    'description': 'View and remove logged-in devices',
                },
            },
            'privacy': {
                'soft_wall_deal_preview': {
                    'enabled': investor_profile.soft_wall_deal_preview,
                    'description': 'Show teaser info before full KYC',
                },
                'discovery_opt_in': {
                    'enabled': investor_profile.discovery_opt_in,
                    'description': 'Allow syndicate leads outside network to invite you',
                },
                'anonymity_preference': {
                    'enabled': investor_profile.anonymity_preference,
                    'description': 'Hide name from other LPs in same SPV',
                },
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def investor_change_password(request):
    """
    Change investor password
    
    POST /api/investors/settings/change-password/ - Change password
    
    POST Payload:
    {
        "current_password": "old_password_here",
        "new_password": "new_password_here",
        "confirm_password": "new_password_here"
    }
    """
    user = request.user
    
    # Get investor profile to ensure user has completed onboarding
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    data = request.data
    
    # Validate required fields
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not current_password:
        return Response({
            'error': 'Current password is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not new_password:
        return Response({
            'error': 'New password is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not confirm_password:
        return Response({
            'error': 'Password confirmation is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify current password
    if not user.check_password(current_password):
        return Response({
            'error': 'Current password is incorrect'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if new password matches confirmation
    if new_password != confirm_password:
        return Response({
            'error': 'New password and confirmation password do not match'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if new password is different from current password
    if user.check_password(new_password):
        return Response({
            'error': 'New password must be different from current password'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate new password strength using Django's password validators
    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        errors = list(e.messages)
        return Response({
            'error': 'Password validation failed',
            'details': errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({
        'success': True,
        'message': 'Password changed successfully'
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def investor_communication_settings(request):
    """
    Get or update investor communication settings
    
    GET /api/investors/settings/communication/ - Get current communication settings
    PUT /api/investors/settings/communication/ - Update communication settings
    
    PUT/PATCH Payload:
    {
        "preferred_contact_method": "email",
        "update_frequency": "weekly",
        "event_alerts": {
            "capital_calls": true,
            "secondary_offers": true,
            "portfolio_updates": true,
            "distributions": true
        },
        "marketing_consent": false
    }
    """
    user = request.user
    
    try:
        investor_profile = InvestorProfile.objects.get(user=user)
    except InvestorProfile.DoesNotExist:
        return Response({
            'error': 'Investor profile not found. Please complete onboarding first.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        # Default event alerts if not set
        event_alerts = investor_profile.event_alerts or {
            'capital_calls': True,
            'secondary_offers': True,
            'portfolio_updates': True,
            'distributions': True,
        }
        
        response_data = {
            'success': True,
            'communication': {
                'preferred_contact_method': investor_profile.preferred_contact_method,
                'preferred_contact_method_display': investor_profile.get_preferred_contact_method_display(),
                'contact_method_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.CONTACT_METHOD_CHOICES],
                'update_frequency': investor_profile.update_frequency,
                'update_frequency_display': investor_profile.get_update_frequency_display(),
                'update_frequency_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.UPDATE_FREQUENCY_CHOICES],
                'event_alerts': {
                    'capital_calls': {
                        'enabled': event_alerts.get('capital_calls', True),
                        'description': 'Investment funding requests',
                    },
                    'secondary_offers': {
                        'enabled': event_alerts.get('secondary_offers', True),
                        'description': 'Secondary market opportunities',
                    },
                    'portfolio_updates': {
                        'enabled': event_alerts.get('portfolio_updates', True),
                        'description': 'Performance and valuation changes',
                    },
                    'distributions': {
                        'enabled': event_alerts.get('distributions', True),
                        'description': 'Dividend and return payments',
                    },
                },
                'marketing_consent': {
                    'enabled': investor_profile.marketing_consent,
                    'description': 'Product updates and partner offers',
                },
            },
        }
        
        return Response(response_data)
    
    elif request.method in ['PUT', 'PATCH']:
        data = request.data
        
        # Validate preferred_contact_method
        if 'preferred_contact_method' in data:
            contact_method = data['preferred_contact_method']
            valid_methods = [choice[0] for choice in InvestorProfile.CONTACT_METHOD_CHOICES]
            if contact_method not in valid_methods:
                return Response({
                    'error': f'Invalid contact method. Must be one of: {", ".join(valid_methods)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            investor_profile.preferred_contact_method = contact_method
        
        # Validate update_frequency
        if 'update_frequency' in data:
            frequency = data['update_frequency']
            valid_frequencies = [choice[0] for choice in InvestorProfile.UPDATE_FREQUENCY_CHOICES]
            if frequency not in valid_frequencies:
                return Response({
                    'error': f'Invalid update frequency. Must be one of: {", ".join(valid_frequencies)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            investor_profile.update_frequency = frequency
        
        # Validate event_alerts
        if 'event_alerts' in data:
            event_alerts_data = data['event_alerts']
            if not isinstance(event_alerts_data, dict):
                return Response({
                    'error': 'event_alerts must be a dictionary with capital_calls, secondary_offers, portfolio_updates, and distributions keys'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Ensure all keys exist with boolean values
            validated_event_alerts = {
                'capital_calls': bool(event_alerts_data.get('capital_calls', True)),
                'secondary_offers': bool(event_alerts_data.get('secondary_offers', True)),
                'portfolio_updates': bool(event_alerts_data.get('portfolio_updates', True)),
                'distributions': bool(event_alerts_data.get('distributions', True)),
            }
            investor_profile.event_alerts = validated_event_alerts
        
        # Validate marketing_consent
        if 'marketing_consent' in data:
            investor_profile.marketing_consent = bool(data['marketing_consent'])
        
        investor_profile.save()
        
        event_alerts = investor_profile.event_alerts or {
            'capital_calls': True,
            'secondary_offers': True,
            'portfolio_updates': True,
            'distributions': True,
        }
        
        response_data = {
            'success': True,
            'message': 'Communication settings updated successfully',
            'communication': {
                'preferred_contact_method': investor_profile.preferred_contact_method,
                'preferred_contact_method_display': investor_profile.get_preferred_contact_method_display(),
                'contact_method_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.CONTACT_METHOD_CHOICES],
                'update_frequency': investor_profile.update_frequency,
                'update_frequency_display': investor_profile.get_update_frequency_display(),
                'update_frequency_choices': [{'value': choice[0], 'label': choice[1]} for choice in InvestorProfile.UPDATE_FREQUENCY_CHOICES],
                'event_alerts': {
                    'capital_calls': {
                        'enabled': event_alerts.get('capital_calls', True),
                        'description': 'Investment funding requests',
                    },
                    'secondary_offers': {
                        'enabled': event_alerts.get('secondary_offers', True),
                        'description': 'Secondary market opportunities',
                    },
                    'portfolio_updates': {
                        'enabled': event_alerts.get('portfolio_updates', True),
                        'description': 'Performance and valuation changes',
                    },
                    'distributions': {
                        'enabled': event_alerts.get('distributions', True),
                        'description': 'Dividend and return payments',
                    },
                },
                'marketing_consent': {
                    'enabled': investor_profile.marketing_consent,
                    'description': 'Product updates and partner offers',
                },
            },
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
