from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('transition/<str:app_label>/<str:model_name>/<int:object_id>/<int:transition_id>/', views.execute_transition, name='execute_transition'),
    path('backup/', views.backup_dashboard, name='backup_dashboard'),
    path('backup/download/', views.download_backup, name='download_backup'),
    path('settings/', views.settings_dashboard, name='settings_dashboard'),
    path('settings/config/<int:pk>/', views.update_config, name='update_config'),
]
