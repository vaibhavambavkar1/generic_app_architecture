from django.urls import path
from . import views, crud

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('po/', views.po_list, name='po_list'),
    path('po/<int:pk>/', views.po_detail, name='po_detail'),
    path('po/<int:pk>/pdf/', views.po_pdf_export, name='po_pdf_export'),
    path('po/export/<str:fmt>/', views.po_bulk_export, name='po_bulk_export'),
    path('items/import/', views.item_import, name='item_import'),
    path('dashboard/chart/', views.dashboard_chart, name='dashboard_chart'),
    path('dashboard/valuation-chart/', views.inventory_valuation_chart, name='inventory_valuation_chart'),
    path('items/', views.item_list, name='item_list'),
    path('scan/', views.barcode_scan, name='barcode_scan'),
    path('po/create/', views.po_create, name='po_create'),
    path('po/add-row/', views.po_add_item_row, name='po_add_item_row'),
    
    # Generic CRUD
    path('manage/<str:model_name>/', crud.manage_list, name='manage_list'),
    path('manage/<str:model_name>/create/', crud.manage_create, name='manage_create'),
    path('manage/<str:model_name>/<int:pk>/update/', crud.manage_update, name='manage_update'),
    path('manage/<str:model_name>/<int:pk>/delete/', crud.manage_delete, name='manage_delete'),
]
