from django.views.generic import View
from django.db.models import Q, F
from django.contrib.sessions.backends.db import SessionStore

from .models import (
    Cart,
    CartProduct,
    ColoredProduct,
    Collection,
)


class CartMixin(View):

    def dispatch(self, request, *args, **kwargs):
        user_ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if user_ip_address:
            ip = user_ip_address.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        current_session_key = request.session.session_key
        if current_session_key is None:
            request.session.save()
            current_session_key = request.session.session_key
        self.cart, created = Cart.objects.filter(paid=False).only('total_products', 'final_price', 'paid',).get_or_create(owner=ip, session_key=current_session_key, paid=False)

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
            ).distinct().order_by('-pub_date', '-sort_order').defer(
                'id', 'is_active', 'sort_order', 'product_id',
                'product__is_active', 'product__pub_date',
            )[:6]
        return super().dispatch(request, *args, **kwargs)


class CollectionsMixin(View):

    def dispatch(self, request, *args, **kwargs):
        self.collections = Collection.objects.filter(is_active=True).order_by('-sort_order')
        return super().dispatch(request, *args, **kwargs)


class CatalogMixin(View):

    def dispatch(self, request, *args, **kwargs):
        self.catalog_slug = kwargs.get('catalog_slug')
        catalog_filters = Q(is_active=True) & Q(product__is_active=True) & \
                Q(product__collection__is_active=True) & \
                Q(images__is_active=True)

        if self.catalog_slug is not None:
            collection = Collection.objects.filter(slug=self.catalog_slug).first()
            if collection is not None:
                catalog_filters = catalog_filters & Q(product__collection=collection)

        self.catalog_products = ColoredProduct.objects.select_related('product')  \
            .prefetch_related('images').prefetch_related('product__sizes').filter(
                catalog_filters
            ).distinct()
        sorting = '-pub_date', '-sort_order'
        price = request.GET.get('price')
        newer = request.GET.get('newer')

        if newer is not None:
            if newer == "down":
                sorting = ('-pub_date', )
            else:
                sorting = ('pub_date', )

        if price is not None:
            if price == "down":
                sorting = ('-price', )
            else:
                sorting = ('price', )

        """sorting = (F('old_price') - F('price'), )
        sorting = (F('price') - F('old_price'), )
        print(*sorting)"""

        self.catalog_products = self.catalog_products.order_by(*sorting).defer(
            'id', 'is_active', 'sort_order', 'product_id',
            'product__is_active', 'product__pub_date',
        )

        return super().dispatch(request, *args, **kwargs)
