from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Quotations & SOs
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/new/', views.quotation_create_modal, name='quotation_create_modal'),
    path('quotations/<int:pk>/', views.quotation_detail, name='quotation_detail'),
    path('quotations/<int:pk>/add-item/', views.quotation_add_item, name='quotation_add_item'),
    path('quotations/item/<int:item_pk>/delete/', views.quotation_delete_item, name='quotation_delete_item'),
    path('quotations/<int:pk>/send/', views.quotation_send_modal, name='quotation_send_modal'),
    
    path('orders/', views.sales_order_list, name='sales_order_list'),
    path('orders/new/', views.sales_order_create_modal, name='sales_order_create_modal'),
    path('orders/<int:pk>/', views.sales_order_detail, name='sales_order_detail'),
    
    # POS Terminal
    path('pos/', views.pos_terminal, name='pos_terminal'),
    path('pos/scan/', views.pos_scan_barcode, name='pos_scan_barcode'),
    path('pos/remove/<int:item_id>/', views.pos_remove_item, name='pos_remove_item'),
    path('pos/checkout/', views.pos_checkout, name='pos_checkout'),
    path('pos/receipt/<int:pk>/', views.pos_receipt, name='pos_receipt'),
]
