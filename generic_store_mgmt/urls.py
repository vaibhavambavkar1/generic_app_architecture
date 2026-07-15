from django.urls import path
from . import views

app_name = 'generic_store_mgmt'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
]
