from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransferViewSet, TransferDocumentViewSet

router = DefaultRouter()
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'transfer-documents', TransferDocumentViewSet, basename='transfer-document')

urlpatterns = [
    path('', include(router.urls)),
]

