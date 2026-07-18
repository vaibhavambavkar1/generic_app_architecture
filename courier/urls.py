from django.urls import path
from . import views

app_name = 'courier'

urlpatterns = [
    path('dashboard/', views.dispatcher_dashboard, name='dispatcher_dashboard'),
    path('manifest/<int:manifest_id>/add-waybill/', views.add_waybill_to_manifest, name='add_waybill_to_manifest'),
    path('waybill/<int:waybill_id>/pdf/', views.download_waybill_pdf, name='download_waybill_pdf'),
]
