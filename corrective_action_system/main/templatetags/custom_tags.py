# templatetags/custom_tags.py
from django import template

register = template.Library()


@register.filter(name='get_item')
def get_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""


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

