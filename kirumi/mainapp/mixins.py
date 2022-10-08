import requests
import csv
from datetime import datetime

from django.db import transaction
from django.db.models import Q, F
from django.urls import reverse
from django.core.cache import cache
from django.http import HttpResponseRedirect
from django.views.generic import View

from .models import (
    Cart,
    CartProduct,
    ColoredProduct,
    Collection,
    Order,
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
            request.session.create()
            current_session_key = request.session.session_key
        self.cart, created = Cart.objects  \
            .only('total_products', 'final_price', 'paid', 'promocode')  \
            .get_or_create(owner=ip, session_key=current_session_key, paid=False)

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

        if self.catalog_slug == "hoodie":
            catalog_filters = catalog_filters & Q(variation__id=2)

        self.catalog_products = ColoredProduct.objects.select_related('product')  \
            .prefetch_related('images').prefetch_related('product__sizes').filter(
                catalog_filters
            ).distinct()
        sorting = '-pub_date', '-sort_order'
        price = request.GET.get('price')
        newer = request.GET.get('newer')
        discount = request.GET.get('discount')

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

        if discount is not None:
            if discount == "down":
                sorting = (((F('old_price') - F('price'))*100/F('old_price')).desc(nulls_last=True), )
            else:
                sorting = ((F('old_price') - F('price'))*100/F('old_price'), )

        self.catalog_products = self.catalog_products.order_by(*sorting).defer(
            'id', 'is_active', 'sort_order', 'product_id',
            'product__is_active', 'product__pub_date',
        )

        return super().dispatch(request, *args, **kwargs)


class PaymentMixin(View):

    def dispatch(self, request, *args, **kwargs):
        if self.products_in_cart.count() == 0:
            return HttpResponseRedirect(reverse('cart'))

        self.order = Order.objects.filter(id=self.cart.order_id).first()
        use_old_order_data = False
        self.firstName = request.POST.get('firstName')
        self.lastName = request.POST.get('lastName')
        self.email = request.POST.get('email')
        self.phone = request.POST.get('phone')
        self.chosenPost = request.POST.get('chosenPost')  # номер поста
        self.addresPost = request.POST.get('addresPost')  # адрес
        self.pricePost = request.POST.get('pricePost')  # стоимость доставки
        self.timePost = request.POST.get('timePost')  # приблизительное время доставки

        required_params_list = [
            self.firstName, self.lastName, self.email, self.phone,
            self.addresPost, self.pricePost, self.timePost,
        ]
        null_param = False
        for param in required_params_list:
            if param is None or param=="":
                null_param = True

        if null_param:
            if self.order is None:
                return HttpResponseRedirect(reverse('checkout'))
            else:
                use_old_order_data = True

        if use_old_order_data:
            self.firstName = self.order.first_name
            self.lastName = self.order.last_name
            self.email = self.order.email
            self.phone = self.order.phone
            self.chosenPost = ''  # номер поста
            self.addresPost = self.order.address  # адрес
            self.pricePost = 200  # стоимость доставки
            self.timePost = '1 - 2'  # приблизительное время доставки
        else:
            BUYING_TYPE_SELF = 'SELF'
            self.order, _ = Order.objects.get_or_create(
                first_name=self.firstName, last_name=self.lastName, email=self.email,
                phone=self.phone, address=self.addresPost, buying_type=BUYING_TYPE_SELF,
                paid=False,
            )
            self.cart.order_id = self.order.id
            self.cart.save()

        return super().dispatch(request, *args, **kwargs)


class OrderMixin(View):

    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        self.order = Order.objects.filter(id=self.cart.order_id).first()
        if self.order is None:
            return HttpResponseRedirect(reverse('checkout'))
        self.cart.paid = True
        self.order.paid = True
        self.order.paid_datetime = datetime.now()
        STATUS_IN_PROGRESS = 'IN PROGRESS'
        self.order.status = STATUS_IN_PROGRESS
        self.cart.save()
        self.order.save()
        request.session.flush()
        return super().dispatch(request, *args, **kwargs)


class CachedCitiesMixin(View):

    def dispatch(self, request, *args, **kwargs):
        CSV_URL = 'https://raw.githubusercontent.com/hflabs/city/master/city.csv'
        self.cities_dict = {}

        self.cities_dict = cache.get('cities_dict')
        if self.cities_dict is None:
            self.cities_dict = {}
            with requests.get(CSV_URL, stream=True) as r:
                lines = (line.decode('utf-8') for line in r.iter_lines())
                for row in csv.reader(lines):
                    self.cities_dict[str(row[12])] = str(row[0])

            if len(self.cities_dict)>1:
                with open('cities.csv', 'w', newline='') as file:
                    writer = csv.writer(file)
                    for dict_value in self.cities_dict.items():
                        writer.writerow(dict_value)
            else:
                with open('cities.csv', 'r', newline='') as file:
                    for row in csv.reader(file):
                        self.cities_dict[str(row[0])] = str(row[1])
            del self.cities_dict['kladr_id']

            cache.set('cities_dict', self.cities_dict, 60*60*24)

        return super().dispatch(request, *args, **kwargs)
