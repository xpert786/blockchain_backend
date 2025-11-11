from django.urls import path
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
    list_company_stages,
    list_incorporation_types,
    list_instrument_types,
    list_share_classes,
    list_rounds,
    list_master_partnership_entities,
    spv_dashboard_summary,
    spv_management_overview,
)

spv_list = SPVViewSet.as_view({'get': 'list', 'post': 'create'})
spv_detail = SPVViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})
spv_my_spvs = SPVViewSet.as_view({'get': 'my_spvs'})
spv_update_status = SPVViewSet.as_view({'patch': 'update_status'})
spv_update_step2 = SPVViewSet.as_view({'patch': 'update_step2'})
spv_update_step3 = SPVViewSet.as_view({'patch': 'update_step3'})
spv_update_step4 = SPVViewSet.as_view({'patch': 'update_step4'})
spv_update_step5 = SPVViewSet.as_view({'patch': 'update_step5'})

portfolio_company_list = PortfolioCompanyViewSet.as_view({'get': 'list', 'post': 'create'})
portfolio_company_detail = PortfolioCompanyViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy'
})

company_stage_list = CompanyStageViewSet.as_view({'get': 'list', 'post': 'create'})
company_stage_detail = CompanyStageViewSet.as_view({'get': 'retrieve'})

incorporation_type_list = IncorporationTypeViewSet.as_view({'get': 'list', 'post': 'create'})
incorporation_type_detail = IncorporationTypeViewSet.as_view({'get': 'retrieve'})

instrument_type_list = InstrumentTypeViewSet.as_view({'get': 'list', 'post': 'create'})
instrument_type_detail = InstrumentTypeViewSet.as_view({'get': 'retrieve'})

share_class_list = ShareClassViewSet.as_view({'get': 'list', 'post': 'create'})
share_class_detail = ShareClassViewSet.as_view({'get': 'retrieve'})

round_list = RoundViewSet.as_view({'get': 'list', 'post': 'create'})
round_detail = RoundViewSet.as_view({'get': 'retrieve'})

master_partnership_entity_list = MasterPartnershipEntityViewSet.as_view({'get': 'list', 'post': 'create'})
master_partnership_entity_detail = MasterPartnershipEntityViewSet.as_view({'get': 'retrieve'})

urlpatterns = [
    path('spv/', spv_list, name='spv-list'),
    path('spv/<int:pk>/', spv_detail, name='spv-detail'),
    path('spv/my_spvs/', spv_my_spvs, name='spv-my-spvs'),
    path('spv/<int:pk>/update_status/', spv_update_status, name='spv-update-status'),
    path('spv/<int:pk>/update_step2/', spv_update_step2, name='spv-update-step2'),
    path('spv/<int:pk>/update_step3/', spv_update_step3, name='spv-update-step3'),
    path('spv/<int:pk>/update_step4/', spv_update_step4, name='spv-update-step4'),
    path('spv/<int:pk>/update_step5/', spv_update_step5, name='spv-update-step5'),
    path('spv/dashboard/', spv_dashboard_summary, name='spv-dashboard'),
    path('spv/management/', spv_management_overview, name='spv-management'),
    path('portfolio-companies/', portfolio_company_list, name='portfolio-company-list'),
    path('portfolio-companies/<int:pk>/', portfolio_company_detail, name='portfolio-company-detail'),
    path('company-stages/', company_stage_list, name='company-stage-list'),
    path('company-stages/<int:pk>/', company_stage_detail, name='company-stage-detail'),
    path('incorporation-types/', incorporation_type_list, name='incorporation-type-list'),
    path('incorporation-types/<int:pk>/', incorporation_type_detail, name='incorporation-type-detail'),
    path('instrument-types/', instrument_type_list, name='instrument-type-list'),
    path('instrument-types/<int:pk>/', instrument_type_detail, name='instrument-type-detail'),
    path('share-classes/', share_class_list, name='share-class-list'),
    path('share-classes/<int:pk>/', share_class_detail, name='share-class-detail'),
    path('rounds/', round_list, name='round-list'),
    path('rounds/<int:pk>/', round_detail, name='round-detail'),
    path('master-partnership-entities/', master_partnership_entity_list, name='master-partnership-entity-list'),
    path('master-partnership-entities/<int:pk>/', master_partnership_entity_detail, name='master-partnership-entity-detail'),
    path('spv/options/', get_spv_options, name='spv-options'),

    # Lookup endpoints
    path('lookups/company-stages/', list_company_stages, name='lookup-company-stages'),
    path('lookups/incorporation-types/', list_incorporation_types, name='lookup-incorporation-types'),
    path('lookups/instrument-types/', list_instrument_types, name='lookup-instrument-types'),
    path('lookups/share-classes/', list_share_classes, name='lookup-share-classes'),
    path('lookups/rounds/', list_rounds, name='lookup-rounds'),
    path('lookups/master-partnership-entities/', list_master_partnership_entities, name='lookup-master-partnership-entities'),
]

