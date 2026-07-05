class BasePlugin:
    """
    Base class for all domain plugins.
    Modules like Inventory, Courier, etc. will inherit this.
    """
    identifier = ""
    name = ""
    description = ""
    version = "1.0.0"

    def get_menu_items(self):
        """Return a list of menu items for the UI sidebar."""
        return []

    def get_dashboard_widgets(self):
        """Return a list of widgets to display on the main dashboard."""
        return []

    def register_rules(self):
        """Register custom rules (actions/conditions) with the RuleEngine."""
        pass


class PluginRegistry:
    """
    Central registry for discovering and storing active plugins.
    """
    _plugins = {}

    @classmethod
    def register(cls, plugin_class):
        if not issubclass(plugin_class, BasePlugin):
            raise ValueError("Plugin must inherit from BasePlugin")
        if not plugin_class.identifier:
            raise ValueError("Plugin must have a unique identifier")
            
        cls._plugins[plugin_class.identifier] = plugin_class()

    @classmethod
    def get_plugin(cls, identifier):
        return cls._plugins.get(identifier)

    @classmethod
    def get_all_plugins(cls):
        return list(cls._plugins.values())

    @classmethod
    def get_all_menu_items(cls):
        items = []
        for plugin in cls.get_all_plugins():
            items.extend(plugin.get_menu_items())
        return items
