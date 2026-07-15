from core.sdk.registry import BasePlugin, PluginRegistry


class InventoryPlugin(BasePlugin):
    identifier = "inventory"
    name = "Inventory Management"
    description = "Track physical goods, lot reorders, and supplier purchase orders."

    def get_menu_items(self):
        return [
            {"label": "Products", "url": "/inventory/items/"},
            {"label": "Suppliers", "url": "/inventory/suppliers/"},
            {"label": "Purchase Orders", "url": "/inventory/pos/"},
        ]


# Auto-register when this module is imported by autodiscover_plugins()
PluginRegistry.register(InventoryPlugin)

