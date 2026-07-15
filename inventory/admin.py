from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import Supplier, InventoryItem, PurchaseOrder, POLineItem

class SupplierAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('name', 'contact_email', 'phone', 'gst_number', 'is_active')
    search_fields = ('name', 'contact_email', 'gst_number')
    list_filter = ('is_active',)

class InventoryItemAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('sku', 'name', 'stock_level', 'unit_price', 'is_active')
    search_fields = ('sku', 'name')
    list_filter = ('is_active', 'has_expiry_date')

class POLineItemInline(admin.TabularInline):
    model = POLineItem
    extra = 1

class PurchaseOrderAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('po_number', 'supplier', 'total_amount', 'status', 'created_at')
    search_fields = ('po_number', 'supplier__name')
    list_filter = ('status', 'created_at')
    inlines = [POLineItemInline]

admin.site.register(Supplier, SupplierAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
