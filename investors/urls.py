from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestorProfileViewSet
from .dashboard_views import (
    DashboardViewSet,
    PortfolioViewSet,
    InvestmentViewSet,
    NotificationViewSet
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'profiles', InvestorProfileViewSet, basename='investor-profile')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'portfolio', PortfolioViewSet, basename='portfolio')
router.register(r'investments', InvestmentViewSet, basename='investment')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
