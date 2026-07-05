from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'

    def ready(self):
        # Register the plugin with the core SDK
        from core.sdk.registry import PluginRegistry
        from .plugin import InventoryPlugin
        PluginRegistry.register(InventoryPlugin)

        # Register business rules with the Rule Engine
        import inventory.rules
