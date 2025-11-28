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
from spv.models import SPV


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
