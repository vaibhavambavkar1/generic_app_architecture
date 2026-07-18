from django.contrib import admin
from .models import Waybill, DispatchManifest, ManifestItem, ProofOfDelivery

class ManifestItemInline(admin.TabularInline):
    model = ManifestItem
    extra = 1

@admin.register(Waybill)
class WaybillAdmin(admin.ModelAdmin):
    list_display = ('waybill_number', 'sender', 'receiver_name', 'status', 'price')
    list_filter = ('status', 'service_type', 'origin_zone', 'destination_zone')
    search_fields = ('waybill_number', 'receiver_name', 'receiver_phone')

@admin.register(DispatchManifest)
class DispatchManifestAdmin(admin.ModelAdmin):
    list_display = ('manifest_number', 'driver', 'vehicle', 'status', 'date')
    list_filter = ('status', 'date')
    search_fields = ('manifest_number',)
    inlines = [ManifestItemInline]

@admin.register(ProofOfDelivery)
class ProofOfDeliveryAdmin(admin.ModelAdmin):
    list_display = ('waybill', 'received_by', 'timestamp')
    search_fields = ('waybill__waybill_number', 'received_by')
