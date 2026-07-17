from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('setup/', views.setup_wizard, name='setup_wizard'),
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/add/', views.resource_create, name='resource_create'),
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/add/', views.schedule_create, name='schedule_create'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/slots/', views.api_slots, name='api_slots'),
]
