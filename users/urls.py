from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, SyndicateViewSet, SectorViewSet, GeographyViewSet, SyndicateOnboardingViewSet, RegistrationViewSet
from .simple_auth_views import SimpleAuthViewSet
from .registration_views import RegistrationFlowViewSet
from .test_views import TestEmailViewSet
from .debug_views import DebugViewSet
from .syndicate_flow_views import SyndicateFlowViewSet
from .single_syndicate_views import SingleSyndicateViewSet
from .syndicate_image_views import SyndicateImageViewSet
from .cors_views import cors_preflight, CorsView

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'syndicates', SyndicateViewSet, basename='syndicate')
router.register(r'sectors', SectorViewSet, basename='sector')
router.register(r'geographies', GeographyViewSet, basename='geography')
router.register(r'onboarding', SyndicateOnboardingViewSet, basename='onboarding')
router.register(r'registration', RegistrationViewSet, basename='registration')
router.register(r'registration-flow', RegistrationFlowViewSet, basename='registration-flow')
router.register(r'auth', SimpleAuthViewSet, basename='auth')
router.register(r'test-email', TestEmailViewSet, basename='test-email')
router.register(r'debug', DebugViewSet, basename='debug')
router.register(r'syndicate-flow', SyndicateFlowViewSet, basename='syndicate-flow')
router.register(r'single-syndicate', SingleSyndicateViewSet, basename='single-syndicate')
router.register(r'syndicate-images', SyndicateImageViewSet, basename='syndicate-images')

urlpatterns = [
    path('', include(router.urls)),
    # CORS preflight handler
    path('cors-preflight/', cors_preflight, name='cors-preflight'),
]

