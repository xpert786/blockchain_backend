from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet,
    DocumentSignatoryViewSet,
    DocumentTemplateViewSet,
    generate_document_from_template,
    get_generated_documents,
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'document-signatories', DocumentSignatoryViewSet, basename='document-signatory')
router.register(r'document-templates', DocumentTemplateViewSet, basename='document-template')

urlpatterns = [
    path('documents/generate-from-template/', generate_document_from_template),
    path('documents/generated-documents/', get_generated_documents),
    path('', include(router.urls)),
]

