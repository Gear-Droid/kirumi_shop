from django import template


register = template.Library()

@register.filter
def is_active(values):
    values = [val for val in values if val.is_active==True]
    return values
