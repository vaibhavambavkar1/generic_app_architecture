from django.urls import path
from . import views

app_name = 'generic_store_mgmt'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/new/', views.product_create_modal, name='product_create_modal'),
    path('products/<int:pk>/edit/', views.product_edit_modal, name='product_edit_modal'),
    
    path('categories/new/', views.category_create_modal, name='category_create_modal'),
    path('categories/<int:pk>/edit/', views.category_edit_modal, name='category_edit_modal'),
    
    path('brands/new/', views.brand_create_modal, name='brand_create_modal'),
    path('brands/<int:pk>/edit/', views.brand_edit_modal, name='brand_edit_modal'),
    
    path('uoms/new/', views.uom_create_modal, name='uom_create_modal'),
    path('uoms/<int:pk>/edit/', views.uom_edit_modal, name='uom_edit_modal'),
]
