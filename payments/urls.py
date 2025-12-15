from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SPVStripeAccountViewSet, PaymentViewSet, StripeWebhookView

router = DefaultRouter()
router.register(r'stripe-accounts', SPVStripeAccountViewSet, basename='stripe-accounts')
router.register(r'', PaymentViewSet, basename='payments')

urlpatterns = [
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('', include(router.urls)),
]
