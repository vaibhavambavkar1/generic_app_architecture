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
