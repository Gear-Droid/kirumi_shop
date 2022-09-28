from decimal import Decimal
from django import template


register = template.Library()


@register.filter
def sub(val1, val2):
    return val1 - val2


@register.filter
def add_decimal(val1, val2):
    return Decimal(val1) + Decimal(val2)


@register.filter
def comma_to_point(number):
    return str(number)


@register.filter
def to_penny(number):
    return int(float(number)*100)


@register.filter
def show_discount(cart):
    if cart.promocode is None:
        return False
    return cart.final_price!=cart.price_before_discount
