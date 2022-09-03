from modeltranslation.translator import register, TranslationOptions
from .models import *


@register(Banner)
class ProductTranslationOptions(TranslationOptions):
    fields = ('header', 'description', )


@register(Collection)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description', )


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', 'description', )


@register(ColoredProduct)
class ProductTranslationOptions(TranslationOptions):
    fields = ('name', )
