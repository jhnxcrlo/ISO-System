# templatetags/custom_tags.py
from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""

@register.filter
def get_item(dictionary, key):
    """Retrieve a value from a dictionary by key."""
    return dictionary.get(key)

@register.filter
def message_icon(tags):
    """Return SweetAlert icon type based on message tags."""
    return 'success' if 'success' in tags else 'error'



@register.filter(name='add_class')
def add_class(value, css_class):
    return value.as_widget(attrs={'class': css_class})

@register.filter
def get_key(dictionary, key):
    """
    Safely retrieve a value from a dictionary using a key.
    """
    try:
        return dictionary.get(key, "")
    except (AttributeError, TypeError):
        return ""

