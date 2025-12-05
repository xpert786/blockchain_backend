from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestorProfileViewSet
from .dashboard_views import (
    DashboardViewSet,
    PortfolioViewSet,
    InvestmentViewSet,
    NotificationViewSet
)
from .investor_detail_views import (
    investor_detail,
    investor_investments,
    investor_kyc_status,
    investor_risk_profile,
    spv_investment_detail,
    spv_financials,
    spv_team,
    spv_documents,
    investor_identity_settings,
    investor_accreditation_settings,
    investor_tax_compliance_settings,
    investor_eligibility_settings,
    investor_financial_settings,
    investor_portfolio_settings,
    investor_security_privacy_settings,
    investor_change_password,
    investor_communication_settings,
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'profiles', InvestorProfileViewSet, basename='investor-profile')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'portfolio', PortfolioViewSet, basename='portfolio')
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Investor Settings - Must come first to avoid router conflicts
    path('settings/identity/', investor_identity_settings, name='investor-identity-settings'),
    path('settings/accreditation/', investor_accreditation_settings, name='investor-accreditation-settings'),
    path('settings/tax-compliance/', investor_tax_compliance_settings, name='investor-tax-compliance-settings'),
    path('settings/eligibility/', investor_eligibility_settings, name='investor-eligibility-settings'),
    path('settings/financial/', investor_financial_settings, name='investor-financial-settings'),
    path('settings/portfolio/', investor_portfolio_settings, name='investor-portfolio-settings'),
    path('settings/security-privacy/', investor_security_privacy_settings, name='investor-security-privacy-settings'),
    path('settings/change-password/', investor_change_password, name='investor-change-password'),
    path('settings/communication/', investor_communication_settings, name='investor-communication-settings'),
    
    # Investor Detail Endpoints - Must come before router patterns to avoid conflicts
    path('investor/<int:investor_id>/', investor_detail, name='investor-detail'),
    path('investor/<int:investor_id>/investments/', investor_investments, name='investor-investments'),
    path('investor/<int:investor_id>/kyc-status/', investor_kyc_status, name='investor-kyc-status'),
    path('investor/<int:investor_id>/risk-profile/', investor_risk_profile, name='investor-risk-profile'),
    
    # SPV Investment Detail for Discover Deals page (from investor perspective)
    path('investment-opportunity/<int:spv_id>/', spv_investment_detail, name='spv-investment-detail'),
    path('investment-opportunity/<int:spv_id>/financials/', spv_financials, name='spv-financials'),
    path('investment-opportunity/<int:spv_id>/team/', spv_team, name='spv-team'),
    path('investment-opportunity/<int:spv_id>/documents/', spv_documents, name='spv-documents'),
    
    # Router patterns
    path('', include(router.urls)),
]
