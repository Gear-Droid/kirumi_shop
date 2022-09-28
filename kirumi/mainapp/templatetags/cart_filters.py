from django import template


register = template.Library()


@register.filter
def sub(val1, val2):
    return val1 - val2


@register.filter
def comma_to_point(number):
    return str(number)


@register.filter
def to_penny(number):
    return int(float(number)*100)
