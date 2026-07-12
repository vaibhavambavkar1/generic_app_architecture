from django import template
from core.sdk.registry import PluginRegistry

register = template.Library()

@register.simple_tag
def get_sidebar_menus():
    """
    Dynamically fetches all menu items registered by active plugins.
    """
    return PluginRegistry.get_all_menu_items()

@register.filter(name='add_class')
def add_class(value, arg):
    """Adds a CSS class to a form field widget."""
    css_classes = value.field.widget.attrs.get('class', '')
    if css_classes:
        css_classes = f"{css_classes} {arg}"
    else:
        css_classes = arg
    return value.as_widget(attrs={'class': css_classes})
