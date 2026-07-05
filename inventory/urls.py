from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('po/', views.po_list, name='po_list'),
    path('po/<int:pk>/', views.po_detail, name='po_detail'),
    path('po/<int:pk>/pdf/', views.po_pdf_export, name='po_pdf_export'),
    path('po/export/<str:fmt>/', views.po_bulk_export, name='po_bulk_export'),
    path('items/import/', views.item_import, name='item_import'),
    path('dashboard/chart/', views.dashboard_chart, name='dashboard_chart'),
]
