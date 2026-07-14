from core.reports.registry import BaseReport
from .models import InventoryItem, PurchaseOrder

class InventoryItemReport(BaseReport):
    name = "Inventory Item Report"
    description = "Detailed list and aggregates of physical inventory items."
    model = InventoryItem

    def get_fields(self):
        return {
            'sku': 'SKU',
            'name': 'Product Name',
            'stock_level': 'Current Stock',
            'reorder_threshold': 'Reorder Level',
            'unit_price': 'Unit Price',
            'is_active': 'Is Active'
        }

    def get_group_by_fields(self):
        return ['is_active', 'has_expiry_date']


class PurchaseOrderReport(BaseReport):
    name = "Purchase Order Report"
    description = "Historical analysis of purchase orders and financial valuations."
    model = PurchaseOrder

    def get_fields(self):
        return {
            'po_number': 'PO Number',
            'supplier__name': 'Supplier Name',
            'total_amount': 'Total Amount (Rs.)',
            'created_at': 'Created Date'
        }

    def get_group_by_fields(self):
        return ['supplier__name']
