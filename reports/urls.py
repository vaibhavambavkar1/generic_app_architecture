from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.executive_dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
]
