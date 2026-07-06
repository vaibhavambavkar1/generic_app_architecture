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
            {'label': 'Items Catalog', 'url': '/inventory/items/', 'icon': 'list'},
            {'label': 'Manage Vendors', 'url': '/inventory/manage/vendor/', 'icon': 'users'},
            {'label': 'Manage Warehouses', 'url': '/inventory/manage/warehouse/', 'icon': 'home'},
            {'label': 'Manage Categories', 'url': '/inventory/manage/category/', 'icon': 'tag'},
            {'label': 'Manage UOMs', 'url': '/inventory/manage/unitofmeasure/', 'icon': 'scale'},
            {'label': 'Manage Locations', 'url': '/inventory/manage/location/', 'icon': 'map-pin'},
        ]
