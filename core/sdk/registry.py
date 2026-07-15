import importlib
import logging

from django.apps import apps as django_apps

logger = logging.getLogger(__name__)


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
    _discovered = False

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

    @classmethod
    def autodiscover(cls):
        """
        Scans all installed Django apps for a `plugins.py` module.
        If found, imports it — which triggers any PluginRegistry.register()
        calls defined at module level in that file.
        
        Usage (in core/apps.py ready()):
            PluginRegistry.autodiscover()
        """
        if cls._discovered:
            return

        for app_config in django_apps.get_app_configs():
            module_name = f"{app_config.name}.plugins"
            try:
                importlib.import_module(module_name)
                logger.info(f"[PluginRegistry] Auto-discovered plugin module: {module_name}")
            except ImportError:
                # App doesn't have a plugins.py — that's fine, skip silently
                pass

        cls._discovered = True


def autodiscover_plugins():
    """
    Module-level convenience function to trigger plugin auto-discovery.
    Call this from core's AppConfig.ready() to auto-register all plugins
    and reports from installed apps.
    """
    PluginRegistry.autodiscover()
    _autodiscover_reports()


def _autodiscover_reports():
    """
    Scans all installed Django apps for a `reports.py` module.
    If found, imports it — which triggers any ReportRegistry.register()
    calls defined at module level in that file.
    """
    for app_config in django_apps.get_app_configs():
        module_name = f"{app_config.name}.reports"
        try:
            importlib.import_module(module_name)
            logger.info(f"[ReportRegistry] Auto-discovered report module: {module_name}")
        except ImportError:
            pass

