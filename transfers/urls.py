from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TransferViewSet,
    TransferDocumentViewSet,
    TransferAgreementDocumentViewSet,
    RequestViewSet,
    RequestDocumentViewSet,
    # Function-based views
    spv_cap_table,
    ownership_chain,
    my_transfers,
    pending_actions,
)

router = DefaultRouter()
router.register(r'transfers', TransferViewSet, basename='transfer')
router.register(r'transfer-documents', TransferDocumentViewSet, basename='transfer-document')
router.register(r'transfer-agreement-documents', TransferAgreementDocumentViewSet, basename='transfer-agreement-document')
router.register(r'requests', RequestViewSet, basename='request')
router.register(r'request-documents', RequestDocumentViewSet, basename='request-document')

urlpatterns = [
    # Router URLs (includes all ViewSet actions)
    path('', include(router.urls)),
    
    # Cap Table & Ownership Chain
    path('cap-table/<int:spv_id>/', spv_cap_table, name='spv-cap-table'),
    path('ownership-chain/<int:spv_id>/<int:investor_id>/', ownership_chain, name='ownership-chain'),
    
    # User-specific transfer views
    path('my-transfers/', my_transfers, name='my-transfers'),
    path('pending-actions/', pending_actions, name='pending-actions'),
]

