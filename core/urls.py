from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('transition/<str:app_label>/<str:model_name>/<int:object_id>/<int:transition_id>/', views.execute_transition, name='execute_transition'),
]
