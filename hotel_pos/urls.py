from django.urls import path
from . import views

app_name = 'hotel_pos'

urlpatterns = [
    path('tables/', views.table_dashboard, name='table_dashboard'),
    path('dashboard/', views.pos_dashboard, name='pos_dashboard'),
    path('dashboard/<int:table_id>/', views.pos_dashboard, name='pos_dashboard_table'),
    path('kds/', views.kitchen_display_system, name='kds'),
    path('receipt/<int:order_id>/', views.receipt_printer, name='receipt_printer'),
    path('add-item/<int:order_id>/<int:item_id>/', views.add_to_order, name='add_to_order'),
    path('send-to-kitchen/<int:order_id>/', views.send_to_kitchen, name='send_to_kitchen'),
    path('generate-bill/<int:order_id>/', views.generate_bill, name='generate_bill'),
    path('mark-item-served/<int:item_id>/', views.mark_item_served, name='mark_item_served'),
]
