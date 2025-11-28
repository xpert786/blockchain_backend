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
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'profiles', InvestorProfileViewSet, basename='investor-profile')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'portfolio', PortfolioViewSet, basename='portfolio')
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    # Investor Detail Endpoints - Must come before router patterns to avoid conflicts
    path('investor/<int:investor_id>/', investor_detail, name='investor-detail'),
    path('investor/<int:investor_id>/investments/', investor_investments, name='investor-investments'),
    path('investor/<int:investor_id>/kyc-status/', investor_kyc_status, name='investor-kyc-status'),
    path('investor/<int:investor_id>/risk-profile/', investor_risk_profile, name='investor-risk-profile'),
    
    # Router patterns
    path('', include(router.urls)),
]
