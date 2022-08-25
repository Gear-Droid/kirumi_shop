from email.mime import image
from django.views.generic import View
from django.db.models import Q, Prefetch

from .models import (
    Cart,
    CartProduct,
    ColoredProduct,
)


class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        self.cart, _ = Cart.objects.only('total_products', 'final_price',).get_or_create(owner=ip)
        return super().dispatch(request, *args, **kwargs)


class CartProductMixin(View):

    def dispatch(self, request, *args, **kwargs):

        self.products_in_cart = CartProduct.objects.filter(
                cart=self.cart, colored_product__images__is_active=True,
            ).select_related('cart').select_related('colored_product').select_related('colored_product__product')  \
            .prefetch_related('colored_product__images').select_related('size').distinct()  \
            .only(
                'cart_id', 'qty', 'colored_product__product_id', 'size__size',
                'colored_product__product__slug',
                'colored_product__product__name', 'colored_product__product__name_ru', 'colored_product__product__name_en',
                'colored_product__slug', 'colored_product__price',
                'colored_product__name', 'colored_product__name_ru', 'colored_product__name_en',
            )

        return super().dispatch(request, *args, **kwargs)


class NewProductsMixin(View):

    def dispatch(self, request, *args, **kwargs):
        self.new_products = ColoredProduct.objects.select_related('product')  \
            .prefetch_related('images').prefetch_related('product__sizes').filter(
                Q(is_active=True) & Q(product__is_active=True) & \
                Q(product__collection__is_active=True) & \
                Q(images__is_active=True)
            ).distinct().order_by('-pub_date').defer(
                'id', 'is_active', 'sort_order', 'product_id',
                'product__is_active', 'product__pub_date',
            )[:6]
        return super().dispatch(request, *args, **kwargs)
