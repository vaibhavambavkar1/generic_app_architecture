from django.urls import path
from . import views

app_name = 'freight'

urlpatterns = [
    path('tracking/<str:booking_number>/', views.freight_tracking, name='tracking'),
]
