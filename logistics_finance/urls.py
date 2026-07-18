from django.urls import path
from . import views

app_name = 'logistics_finance'

urlpatterns = [
    path('dashboard/', views.financial_dashboard, name='dashboard'),
]
