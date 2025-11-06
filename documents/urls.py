from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentViewSet, DocumentSignatoryViewSet

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'document-signatories', DocumentSignatoryViewSet, basename='document-signatory')

urlpatterns = [
    path('', include(router.urls)),
]

