from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('transition/<str:app_label>/<str:model_name>/<int:object_id>/<int:transition_id>/', views.execute_transition, name='execute_transition'),
    path('backup/', views.backup_dashboard, name='backup_dashboard'),
    path('backup/download/', views.download_backup, name='download_backup'),
    path('settings/', views.settings_dashboard, name='settings_dashboard'),
    path('settings/config/<int:pk>/', views.update_config, name='update_config'),
    path('license/activate/', views.activate_license, name='activate_license'),
    path('profile/', views.profile_view, name='profile'),
    path('organization/setup/', views.organization_setup, name='organization_create'),
    
    # Reports Routes
    path('reports/builder/', views.report_builder, name='report_builder'),
    path('reports/fields/', views.load_report_fields, name='load_report_fields'),
    path('reports/filter-row/', views.add_filter_row, name='add_filter_row'),
    path('reports/aggregate-row/', views.add_aggregate_row, name='add_aggregate_row'),
    path('reports/preview/', views.report_preview, name='report_preview'),
    path('reports/save/', views.save_report, name='save_report'),
    path('reports/saved/<int:pk>/', views.execute_saved_report, name='execute_saved_report'),
    path('reports/saved/<int:pk>/delete/', views.delete_saved_report, name='delete_saved_report'),
    path('reports/export/', views.export_report, name='export_report'),
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit_logs'),
    path('search/', views.global_search, name='global_search'),
    
    # Workflow & RBAC Administration
    path('workflow-dashboard/', views.workflow_dashboard, name='workflow_dashboard'),
    path('workflow/transition/<int:transition_id>/edit/', views.edit_transition_row, name='edit_transition_row'),
    path('workflow/transition/<int:transition_id>/cancel/', views.cancel_edit_transition_row, name='cancel_edit_transition_row'),
    path('workflow/transition/<int:transition_id>/update/', views.update_approval_route, name='update_approval_route'),
]

# HTML Auth URLs
from . import auth_html_views
html_auth_patterns = [
    path('auth/login/', auth_html_views.login_view, name='login'),
    path('auth/logout/', auth_html_views.logout_view, name='logout'),
    path('auth/signup/', auth_html_views.signup_view, name='signup'),
    path('auth/forgot-password/', auth_html_views.forgot_password_view, name='forgot_password'),
    path('auth/reset-password/', auth_html_views.reset_password_view, name='reset_password'),
]
urlpatterns += html_auth_patterns

# API URLs
from . import api_views
from rest_framework_simplejwt.views import TokenRefreshView

api_urlpatterns = [
    path('api/auth/login/', api_views.CustomTokenObtainPairView.as_view(), name='api_login'),
    path('api/auth/login/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/auth/signup/', api_views.SignupView.as_view(), name='api_signup'),
    path('api/auth/forgot-password/question/', api_views.ForgotPasswordQuestionView.as_view(), name='api_forgot_password_question'),
    path('api/auth/forgot-password/reset/', api_views.ResetPasswordView.as_view(), name='api_forgot_password_reset'),
]

urlpatterns += api_urlpatterns
