from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/edit/', views.account_edit, name='account_edit'),
    path('accounts/<int:pk>/delete/', views.account_delete, name='account_delete'),
    path('journal/', views.journal_list, name='journal_list'),
    path('journal/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('journal/<int:pk>/edit/', views.journal_edit, name='journal_edit'),
    path('journal/<int:pk>/delete/', views.journal_delete, name='journal_delete'),
    path('journal/create/', views.journal_create, name='journal_create'),
    path('journal/<int:pk>/post/', views.journal_post, name='journal_post'),
    
    # AR/AP Invoicing
    
    path('invoicing/pay/<str:invoice_type>/<int:pk>/', views.process_invoice_payment, name='process_invoice_payment'),
    path('invoicing/ar/<int:pk>/pdf/', views.generate_b2b_invoice_pdf, name='generate_b2b_invoice_pdf'),
]
