from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransferViewSet,
    TransferDocumentViewSet,
    RequestViewSet,
    RequestDocumentViewSet,
)

router = DefaultRouter()
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'transfer-documents', TransferDocumentViewSet, basename='transfer-document')
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'request-documents', RequestDocumentViewSet, basename='request-document')

urlpatterns = [
    path('', include(router.urls)),
]

