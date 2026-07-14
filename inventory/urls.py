from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('items/', views.item_list, name='item_list'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:pk>/edit/', views.item_update, name='item_update'),
    path('items/<int:pk>/delete/', views.item_delete, name='item_delete'),
    path('items/<int:pk>/price-history/', views.item_price_history, name='item_price_history'),
    
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/toggle-status/', views.supplier_toggle_status, name='supplier_toggle_status'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('suppliers/<int:pk>/catalog/pdf/', views.export_supplier_catalog_pdf, name='export_supplier_catalog_pdf'),
    path('suppliers/<int:pk>/catalog/excel/', views.export_supplier_catalog_excel, name='export_supplier_catalog_excel'),
    path('suppliers/<int:pk>/catalog-modal/', views.supplier_catalog_modal, name='supplier_catalog_modal'),
    path('suppliers/<int:pk>/catalog-add/', views.supplier_catalog_add_product, name='supplier_catalog_add_product'),
    path('suppliers/catalog-remove/<int:entry_pk>/', views.supplier_catalog_remove, name='supplier_catalog_remove'),
    
    path('pos/', views.po_list, name='po_list'),
    path('pos/export/pdf/', views.po_export_pdf, name='po_export_pdf'),
    path('pos/export/excel/', views.po_export_excel, name='po_export_excel'),
    path('pos/<int:pk>/', views.po_detail, name='po_detail'),
    path('pos/<int:pk>/pdf/', views.po_download_pdf, name='po_download_pdf'),
    path('pos/<int:pk>/delete/', views.po_delete, name='po_delete'),
    path('pos/<int:pk>/edit/', views.po_edit, name='po_edit'),
    path('pos/create/', views.po_create, name='po_create'),
    path('pos/auto-generate/', views.auto_generate_pos, name='auto_generate_pos'),
    path('pos/<int:pk>/receive-modal/<int:transition_id>/', views.po_receive_modal, name='po_receive_modal'),
    path('pos/<int:pk>/receive-submit/<int:transition_id>/', views.po_receive_submit, name='po_receive_submit'),
    path('pos/<int:pk>/email-modal/', views.po_email_modal, name='po_email_modal'),
    path('pos/<int:pk>/email-submit/', views.po_email_submit, name='po_email_submit'),
]
