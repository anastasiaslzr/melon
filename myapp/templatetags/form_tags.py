from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='add_attr')
def add_attr(field, attr_string):
    """
    Add arbitrary HTML attributes to a form field widget.

    Usage: {{ form.field|add_attr:"placeholder:Enter your name" }}
           {{ form.field|add_attr:"rows:5" }}
           {{ form.field|add_attr:"class:form-control is-invalid" }}
    """
    if not isinstance(field, BoundField):
        return str(field)

    # Parse "key:value" string
    try:
        key, value = attr_string.split(":", 1)
    except ValueError:
        return field  # if bad format, just return unchanged

    attrs = field.field.widget.attrs.copy()
    if key == "class":
        # append classes instead of replacing
        existing = attrs.get("class", "")
        value = (existing + " " + value).strip()

    attrs[key] = value
    return field.as_widget(attrs=attrs)

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})