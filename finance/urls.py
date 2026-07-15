from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('accounts/', views.account_list, name='account_list'),
    path('journal/', views.journal_list, name='journal_list'),
    path('journal/<int:pk>/', views.journal_detail, name='journal_detail'),
    path('journal/create/', views.journal_create, name='journal_create'),
    path('journal/<int:pk>/post/', views.journal_post, name='journal_post'),
]
