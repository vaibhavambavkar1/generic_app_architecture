from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_pdf
from . import views_reports
from . import views_public
from . import api

router = DefaultRouter()
router.register(r'resources', api.ResourceViewSet, basename='api-resource')
router.register(r'bookings', api.BookingViewSet, basename='api-booking')

app_name = 'bookings'

urlpatterns = [
    # Public Routes
    path('book/', views_public.public_booking, name='public_booking'),
    path('book/api/slots/', views_public.public_api_slots, name='public_api_slots'),
    path('book/checkout/', views_public.public_checkout, name='public_checkout'),
    
    # Admin / Dashboard Routes
    path('', views.dashboard, name='dashboard'),
    path('setup/', views.setup_wizard, name='setup_wizard'),
    path('resources/', views.resource_list, name='resource_list'),
    path('resources/add/', views.resource_create, name='resource_create'),
    path('schedules/', views.schedule_list, name='schedule_list'),
    path('schedules/add/', views.schedule_create, name='schedule_create'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/slots/', views.api_slots, name='api_slots'),
    path('bookings/create/', views.booking_create, name='booking_create'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
    path('bookings/<int:pk>/action/<str:action>/', views.booking_action, name='booking_action'),
    path('bookings/<int:pk>/receipt-pdf/', views_pdf.booking_receipt_pdf, name='booking_receipt_pdf'),
    path('reports/', views_reports.reports_dashboard, name='reports'),
    path('api/v1/', include(router.urls)),
]
