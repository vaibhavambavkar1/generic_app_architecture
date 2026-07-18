from django.contrib import admin
from .models import WarehouseZone, Aisle, Rack, Bin, ClientInventory, PutawayTask, PickList, PickListItem

@admin.register(WarehouseZone)
class WarehouseZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'warehouse', 'zone_type')
    list_filter = ('zone_type', 'warehouse')

@admin.register(Aisle)
class AisleAdmin(admin.ModelAdmin):
    list_display = ('code', 'zone')
    
@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    list_display = ('code', 'aisle')

@admin.register(Bin)
class BinAdmin(admin.ModelAdmin):
    list_display = ('code', 'rack', 'max_weight_kg', 'max_volume_m3')

@admin.register(ClientInventory)
class ClientInventoryAdmin(admin.ModelAdmin):
    list_display = ('client', 'product', 'bin_location', 'quantity')
    list_filter = ('client',)
    search_fields = ('product__name', 'bin_location__code')

@admin.register(PutawayTask)
class PutawayTaskAdmin(admin.ModelAdmin):
    list_display = ('task_number', 'client', 'product', 'target_bin', 'quantity', 'status', 'assigned_to')
    list_filter = ('status', 'client')

class PickListItemInline(admin.TabularInline):
    model = PickListItem
    extra = 1

@admin.register(PickList)
class PickListAdmin(admin.ModelAdmin):
    list_display = ('picklist_number', 'client', 'order_reference', 'status', 'assigned_to')
    list_filter = ('status', 'client')
    inlines = [PickListItemInline]
