from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvestorProfileViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'profiles', InvestorProfileViewSet, basename='investor-profile')

urlpatterns = [
    path('', include(router.urls)),
]
