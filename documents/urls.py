from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentViewSet,
    DocumentSignatoryViewSet,
    DocumentTemplateViewSet,
    SyndicateDocumentDefaultsViewSet,
    DocumentGenerationViewSet,
    generate_document_from_template,
    get_generated_documents,
    get_investors_list,
    get_spvs_list,
)

router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'document-signatories', DocumentSignatoryViewSet, basename='document-signatory')
router.register(r'document-templates', DocumentTemplateViewSet, basename='document-template')
router.register(r'syndicate-document-defaults', SyndicateDocumentDefaultsViewSet, basename='syndicate-document-defaults')
router.register(r'document-generations', DocumentGenerationViewSet, basename='document-generation')

urlpatterns = [
    path('documents/generate-from-template/', generate_document_from_template),
    path('documents/generated-documents/', get_generated_documents),
    path('documents/investors/', get_investors_list),  # GET list of investors for dropdown
    path('documents/spvs/', get_spvs_list),  # GET list of SPVs for dropdown
    path('', include(router.urls)),
]
