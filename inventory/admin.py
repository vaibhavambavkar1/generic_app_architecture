from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Supplier, InventoryItem, PurchaseOrder, POLineItem,
    SupplierCatalogItem, InventoryItemPriceLog, Warehouse,
    Batch, SerialNumber, StockLedger, StockAdjustment, WarehouseTransfer
)

class SupplierCatalogItemInline(admin.TabularInline):
    model = SupplierCatalogItem
    extra = 1

class SupplierAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('name', 'contact_email', 'phone', 'gst_number', 'is_active')
    search_fields = ('name', 'contact_email', 'gst_number')
    list_filter = ('is_active',)
    inlines = [SupplierCatalogItemInline]

class InventoryItemPriceLogInline(admin.TabularInline):
    model = InventoryItemPriceLog
    extra = 0
    readonly_fields = ('price', 'changed_at')
    can_delete = False

class InventoryItemAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('sku', 'name', 'stock_level', 'unit_price', 'is_active')
    search_fields = ('sku', 'name')
    list_filter = ('is_active', 'has_expiry_date')
    inlines = [SupplierCatalogItemInline, InventoryItemPriceLogInline]

class POLineItemInline(admin.TabularInline):
    model = POLineItem
    extra = 1

class PurchaseOrderAdmin(ImportExportModelAdmin, SimpleHistoryAdmin):
    list_display = ('po_number', 'supplier', 'total_amount', 'status', 'created_at')
    search_fields = ('po_number', 'supplier__name')
    list_filter = ('status', 'created_at')
    inlines = [POLineItemInline]

class StockLedgerInline(admin.TabularInline):
    model = StockLedger
    extra = 0
    readonly_fields = ('inventory_item', 'batch', 'transaction_type', 'quantity', 'reference_document', 'timestamp')
    can_delete = False

class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)
    inlines = [StockLedgerInline]

class BatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'inventory_item', 'manufacturing_date', 'expiry_date')
    search_fields = ('batch_number', 'inventory_item__name')
    list_filter = ('manufacturing_date', 'expiry_date')

class SerialNumberAdmin(admin.ModelAdmin):
    list_display = ('serial', 'inventory_item', 'is_sold')
    search_fields = ('serial', 'inventory_item__name')
    list_filter = ('is_sold',)

class StockLedgerAdmin(admin.ModelAdmin):
    list_display = ('inventory_item', 'warehouse', 'transaction_type', 'quantity', 'timestamp')
    search_fields = ('inventory_item__name', 'warehouse__name', 'reference_document')
    list_filter = ('transaction_type', 'warehouse', 'timestamp')

class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('warehouse', 'inventory_item', 'quantity_adjusted', 'status')
    search_fields = ('warehouse__name', 'inventory_item__name', 'reason')
    list_filter = ('status',)

class WarehouseTransferAdmin(admin.ModelAdmin):
    list_display = ('from_warehouse', 'to_warehouse', 'inventory_item', 'quantity', 'status')
    search_fields = ('from_warehouse__name', 'to_warehouse__name', 'inventory_item__name')
    list_filter = ('status',)

admin.site.register(Supplier, SupplierAdmin)
admin.site.register(InventoryItem, InventoryItemAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
admin.site.register(Warehouse, WarehouseAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(SerialNumber, SerialNumberAdmin)
admin.site.register(StockLedger, StockLedgerAdmin)
admin.site.register(StockAdjustment, StockAdjustmentAdmin)
admin.site.register(WarehouseTransfer, WarehouseTransferAdmin)
