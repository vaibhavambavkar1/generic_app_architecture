from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        import inventory.rules
        from core.sdk.registry import PluginRegistry
        from .plugins import InventoryPlugin
        PluginRegistry.register(InventoryPlugin)

        from core.reports.registry import ReportRegistry
        from .reports import InventoryItemReport, PurchaseOrderReport
        ReportRegistry.register('inventory_items', InventoryItemReport)
        ReportRegistry.register('purchase_orders', PurchaseOrderReport)
