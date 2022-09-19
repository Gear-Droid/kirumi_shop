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
