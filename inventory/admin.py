from django.contrib import admin
from .models import Item, PurchaseOrder

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'stock_quantity')
    search_fields = ('name', 'sku')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'item', 'quantity', 'total_cost', 'workflow_state', 'created_at')
    list_filter = ('workflow_state',)
