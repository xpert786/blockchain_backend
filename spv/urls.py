from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SPVViewSet,
    PortfolioCompanyViewSet,
    CompanyStageViewSet,
    IncorporationTypeViewSet,
    InstrumentTypeViewSet,
    ShareClassViewSet,
    RoundViewSet,
    MasterPartnershipEntityViewSet,
    get_spv_options,
)

router = DefaultRouter()
router.register(r'spv', SPVViewSet, basename='spv')
router.register(r'portfolio-companies', PortfolioCompanyViewSet, basename='portfolio-company')
router.register(r'company-stages', CompanyStageViewSet, basename='company-stage')
router.register(r'incorporation-types', IncorporationTypeViewSet, basename='incorporation-type')
router.register(r'instrument-types', InstrumentTypeViewSet, basename='instrument-type')
router.register(r'share-classes', ShareClassViewSet, basename='share-class')
router.register(r'rounds', RoundViewSet, basename='round')
router.register(r'master-partnership-entities', MasterPartnershipEntityViewSet, basename='master-partnership-entity')

urlpatterns = [
    path('', include(router.urls)),
    path('spv/options/', get_spv_options, name='spv-options'),
]

