from decimal import Decimal
from django import template


register = template.Library()


@register.filter
def is_active(values):
    values = [val for val in values if val.is_active==True]
    return values


@register.filter
def distinct_colors(values):
    colors_set = set()
    for val in values:
        if val.color_hex_code not in colors_set:
            colors_set.add(val.color_hex_code)
        else:
            values.remove(val)
    return values


@register.filter
def get_discount(product_color):
    discount = Decimal(0)
    if product_color.old_price is not None:
        discount = Decimal((product_color.old_price - product_color.price) * 100 / product_color.old_price)
        discount = discount.quantize(Decimal('1'))
    return discount


@register.filter
def comma_to_point(number):
    return str(number)


@register.filter
def to_penny(number):
    return int(number*100)