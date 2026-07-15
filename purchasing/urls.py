from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('requests/', views.pr_list, name='pr_list'),
    path('requests/create/', views.pr_create, name='pr_create'),
    path('requests/<int:pk>/', views.pr_detail, name='pr_detail'),
    path('requests/<int:pk>/add-item/', views.pr_add_item, name='pr_add_item'),
    path('requests/item/<int:item_pk>/delete/', views.pr_delete_item, name='pr_delete_item'),
    
    path('grn/', views.grn_list, name='grn_list'),
    path('grn/create/', views.grn_create, name='grn_create'),
    path('grn/<int:pk>/', views.grn_detail, name='grn_detail'),
    path('grn/<int:pk>/add-item/', views.grn_add_item, name='grn_add_item'),
    path('grn/item/<int:item_pk>/delete/', views.grn_delete_item, name='grn_delete_item'),
    path('grn/<int:pk>/approve-modal/', views.grn_approve_modal, name='grn_approve_modal'),
]
