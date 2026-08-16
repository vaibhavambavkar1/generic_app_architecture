from django.urls import path
from . import views

app_name = 'hotel_pos'

urlpatterns = [
    path('dashboard/', views.pos_dashboard, name='pos_dashboard'),
    path('kds/', views.kitchen_display_system, name='kds'),
    path('receipt/<int:order_id>/', views.receipt_printer, name='receipt_printer'),
    path('add-item/<int:item_id>/', views.add_to_order, name='add_to_order'),
]
