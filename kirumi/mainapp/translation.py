from modeltranslation.translator import register, TranslationOptions
from .models import *


@register(Collection)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description', )


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description', )


@register(ColoredProduct)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', )
