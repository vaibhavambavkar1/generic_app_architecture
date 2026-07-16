from django.urls import path
from . import views

app_name = 'generic_store_mgmt'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.product_create_modal, name='product_create_modal'),
    path('products/<int:pk>/edit/', views.product_edit_modal, name='product_edit_modal'),
]
