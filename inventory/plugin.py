from core.sdk.registry import BasePlugin

class InventoryPlugin(BasePlugin):
    identifier = "inventory_module"
    name = "Inventory Management"
    description = "Handles items, stock, and purchase orders."
    version = "1.0.0"

    def get_menu_items(self):
        return [
            {'label': 'Inventory Dashboard', 'url': '/inventory/', 'icon': 'box'},
            {'label': 'Purchase Orders', 'url': '/inventory/po/', 'icon': 'shopping-cart'},
        ]
