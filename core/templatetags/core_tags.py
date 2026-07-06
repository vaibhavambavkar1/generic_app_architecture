from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr_name):
    """Dynamically fetches an attribute from an object."""
    value = getattr(obj, attr_name, '')
    if callable(value):
        return "(Relation)"
    return value

@register.filter
def add_class(field, css_class):
    """Adds a CSS class to a Django form field widget."""
    return field.as_widget(attrs={"class": css_class})
