from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import simple_auth_views
from . import registration_views
from . import password_reset_views
from . import test_views
from . import debug_views
from . import cors_views
from . import syndicate_views
from . import syndicate_settings_views
from . import team_management_views
from . import compliance_views
from .views import GoogleLoginWithRoleView, QuickProfileView, get_kyb_verification_status

# Create router for ViewSets
router = DefaultRouter()
router.register(r'team-members', team_management_views.TeamMemberViewSet, basename='team-member')
router.register(r'compliance-documents', compliance_views.ComplianceDocumentViewSet, basename='compliance-document')

urlpatterns = [
    # User management endpoints
    path('', views.welcome_message, name='user-welcome'),
    path('users/', views.user_list, name='user-list'),
    path('users/<int:pk>/', views.user_detail, name='user-detail'),
    path('users/register/', views.user_register, name='user-register'),
    path('users/login/', views.user_login, name='user-login'),
    
    # Sector management endpoints
    path('sectors/', views.sector_list, name='sector-list'),
    path('sectors/<int:pk>/', views.sector_detail, name='sector-detail'),
    
    # Geography management endpoints
    path('geographies/', views.geography_list, name='geography-list'),
    path('geographies/<int:pk>/', views.geography_detail, name='geography-detail'),
    
    # Registration endpoints
    path('registration/register/', views.registration_register, name='registration-register'),
    path('registration/send_email_verification/', views.send_email_verification, name='send-email-verification'),
    path('registration/verify_email/', views.verify_email, name='verify-email'),
    path('registration/send_two_factor/', views.send_two_factor, name='send-two-factor'),
    path('registration/verify_two_factor/', views.verify_two_factor, name='verify-two-factor'),
    path('registration/accept_terms/', views.accept_terms, name='accept-terms'),
    path('registration/complete_registration/', views.complete_registration, name='complete-registration'),
    path('registration/get_registration_status/', views.get_registration_status, name='get-registration-status'),
    
    # Registration flow endpoints
    path('registration-flow/register/', registration_views.registration_flow_register, name='registration-flow-register'),
    path('registration-flow/choose_verification_method/', registration_views.choose_verification_method, name='choose-verification-method'),
    path('registration-flow/verify_code/', registration_views.verify_code, name='verify-code'),
    path('registration-flow/resend_code/', registration_views.resend_code, name='resend-code'),
    path('registration-flow/get_registration_status/', registration_views.get_registration_status, name='registration-flow-get-status'),
    path('registration-flow/get_terms/', registration_views.get_terms, name='get-terms'),
    path('registration-flow/accept_terms/', registration_views.accept_terms, name='registration-flow-accept-terms'),
    path('registration-flow/get_terms_status/', registration_views.get_terms_status, name='get-terms-status'),
    path('registration-flow/complete_registration/', registration_views.complete_registration, name='registration-flow-complete'),
    
    # Authentication endpoints
    path('auth/login/', simple_auth_views.auth_login, name='auth-login'),
    path('auth/verify_2fa_login/', simple_auth_views.verify_2fa_login, name='verify-2fa-login'),
    path('auth/setup_2fa/', simple_auth_views.setup_2fa, name='setup-2fa'),
    path('auth/verify_setup/', simple_auth_views.verify_setup, name='verify-setup'),
    path('auth/resend_code/', simple_auth_views.resend_code, name='resend-code'),
    path('auth/disable_2fa/', simple_auth_views.disable_2fa, name='disable-2fa'),
    path('auth/get_2fa_status/', simple_auth_views.get_2fa_status, name='get-2fa-status'),
    
    # Password reset endpoints
    path('auth/forgot_password/', password_reset_views.forgot_password, name='forgot-password'),
    path('auth/verify_reset_otp/', password_reset_views.verify_reset_otp, name='verify-reset-otp'),
    path('auth/reset_password/', password_reset_views.reset_password, name='reset-password'),
    path('auth/resend_reset_otp/', password_reset_views.resend_reset_otp, name='resend-reset-otp'),
    
    # User profile endpoints
    path('update-phone/', views.update_user_phone, name='update-user-phone'),
    
    # Test email endpoints
    path('test-email/send_test_email/', test_views.send_test_email, name='send-test-email'),
    path('test-email/send_verification_email/', test_views.send_verification_email, name='send-verification-email'),
    path('test-email/send_2fa_email/', test_views.send_2fa_email, name='send-2fa-email'),
    path('test-email/send_test_sms/', test_views.send_test_sms, name='send-test-sms'),
    
    # Debug endpoints
    path('debug/server_status/', debug_views.server_status, name='server-status'),
    path('debug/database_status/', debug_views.database_status, name='database-status'),
    path('debug/email_status/', debug_views.email_status, name='email-status'),
    path('debug/cors_status/', debug_views.cors_status, name='cors-status'),
    path('debug/check_user_verifications/', debug_views.check_user_verifications, name='check-user-verifications'),
    path('debug/verify_code_debug/', debug_views.verify_code_debug, name='verify-code-debug'),
    
    # Syndicate onboarding endpoints
    path('syndicate/profile/', syndicate_views.get_syndicate_profile, name='get-syndicate-profile'),
    path('syndicate/profile/create/', syndicate_views.create_syndicate_profile, name='create-syndicate-profile'),
    path('syndicate/step1/', syndicate_views.syndicate_step1, name='syndicate-step1'),
    path('syndicate/step1/investment-focus/', syndicate_views.syndicate_step1_investment_focus, name='syndicate-step1-investment-focus'),
    path('syndicate/step2/', syndicate_views.syndicate_step2, name='syndicate-step2'),
    path('syndicate/step3a/', syndicate_views.syndicate_step3a_kyb_details, name='syndicate-step3a'),
    path('syndicate/step3b/', syndicate_views.syndicate_step3b_beneficial_owners, name='syndicate-step3b'),
    path('syndicate/step3b/<int:owner_id>/', syndicate_views.syndicate_step3b_beneficial_owners, name='syndicate-step3b-detail'),
    path('syndicate/step3/', syndicate_views.syndicate_step3, name='syndicate-step3'),
    path('syndicate/step4/', syndicate_views.syndicate_step4, name='syndicate-step4'),
    path('syndicate/progress/', syndicate_views.syndicate_progress, name='syndicate-progress'),
    path('syndicate/sectors-geographies/', syndicate_views.get_sectors_and_geographies, name='get-sectors-geographies'),
    path('syndicate/profile/update/', syndicate_views.update_syndicate_profile, name='update-syndicate-profile'),
    
    # Syndicate settings endpoints
    path('syndicate/settings/overview/', syndicate_settings_views.syndicate_settings_overview, name='syndicate-settings-overview'),
    path('syndicate/settings/general-info/', syndicate_settings_views.syndicate_settings_general_info, name='syndicate-settings-general-info'),
    path('syndicate/settings/team-management/', syndicate_settings_views.syndicate_settings_team_management, name='syndicate-settings-team-management'),
    path('syndicate/settings/kyb-verification/', syndicate_settings_views.syndicate_settings_kyb_verification, name='syndicate-settings-kyb-verification'),
    path('syndicate/settings/compliance/', syndicate_settings_views.syndicate_settings_compliance, name='syndicate-settings-compliance'),
    path('syndicate/settings/jurisdictional/', syndicate_settings_views.syndicate_settings_jurisdictional, name='syndicate-settings-jurisdictional'),
    path('syndicate/settings/jurisdictional/<int:geography_id>/', syndicate_settings_views.syndicate_settings_jurisdictional_detail, name='syndicate-settings-jurisdictional-detail'),
    path('syndicate/settings/portfolio/', syndicate_settings_views.syndicate_settings_portfolio, name='syndicate-settings-portfolio'),
    path('syndicate/settings/portfolio/<int:sector_id>/', syndicate_settings_views.syndicate_settings_portfolio_detail, name='syndicate-settings-portfolio-detail'),
    path('syndicate/settings/notifications/', syndicate_settings_views.syndicate_settings_notifications, name='syndicate-settings-notifications'),
    path('syndicate/settings/notifications/<str:preference_type>/', syndicate_settings_views.syndicate_settings_notifications_detail, name='syndicate-settings-notifications-detail'),
    path('syndicate/settings/fee-recipient/', syndicate_settings_views.syndicate_settings_fee_recipient, name='syndicate-settings-fee-recipient'),
    path('syndicate/settings/fee-recipient/<int:recipient_id>/', syndicate_settings_views.syndicate_settings_fee_recipient_detail, name='syndicate-settings-fee-recipient-detail'),
    path('syndicate/settings/bank-details/', syndicate_settings_views.syndicate_settings_bank_details, name='syndicate-settings-bank-details'),
    path('syndicate/settings/bank-details/card/<int:card_id>/', syndicate_settings_views.syndicate_settings_bank_card_detail, name='syndicate-settings-bank-card-detail'),
    path('syndicate/settings/bank-details/account/<int:account_id>/', syndicate_settings_views.syndicate_settings_bank_account_detail, name='syndicate-settings-bank-account-detail'),
    
    # CORS preflight handler
    path('cors-preflight/', cors_views.cors_preflight, name='cors-preflight'),
    # Backwards-compatible alias: original endpoint maps to signin
    path('auth/google/', GoogleLoginWithRoleView.as_view(), name='google_login'),
    path('profile/quick-setup/', QuickProfileView.as_view(), name='quick-profile-setup'),
    path('user/kyb-status/', get_kyb_verification_status, name='kyb-status'),
    
    # Include router URLs for ViewSets
    path('', include(router.urls)),
]