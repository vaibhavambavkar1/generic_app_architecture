from django import template
from core.sdk.registry import PluginRegistry

register = template.Library()

@register.simple_tag
def get_sidebar_menus():
    """
    Dynamically fetches all menu items registered by active plugins.
    """
    return PluginRegistry.get_all_menu_items()
