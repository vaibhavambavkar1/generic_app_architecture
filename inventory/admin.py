from django.contrib import admin
from .models import Item, PurchaseOrder, Vendor, PurchaseOrderItem

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'stock_quantity')
    search_fields = ('name', 'sku')

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'vendor', 'total_amount', 'workflow_state', 'created_at')
    list_filter = ('workflow_state',)
    inlines = [PurchaseOrderItemInline]
