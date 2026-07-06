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

from django.utils.safestring import mark_safe

@register.simple_tag
def icon(name, css_class="w-5 h-5"):
    """Returns an SVG icon string based on the name provided (Heroicons)."""
    icons = {
        'edit': f'<svg class="{css_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path></svg>',
        'delete': f'<svg class="{css_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>',
        'add': f'<svg class="{css_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>',
        'save': f'<svg class="{css_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>',
        'export': f'<svg class="{css_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>',
        'search': f'<svg class="{css_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>',
        'scan': f'<svg class="{css_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M3 14h18M5 6h14a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2z"></path></svg>',
    }
    return mark_safe(icons.get(name, ''))

@register.simple_tag
def get_elided_page_range(paginator, number, on_each_side=1, on_ends=1):
    return paginator.get_elided_page_range(number, on_each_side=on_each_side, on_ends=on_ends)
