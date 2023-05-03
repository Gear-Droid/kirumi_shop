import requests
import csv
import hashlib

from datetime import datetime

from django.conf import settings
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
    OrderProduct,
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
                Q(images__is_active=True) & (  \
                    (Q(product__collection__slug="hoodie") & Q(variation__id=2)) |  \
                    ~Q(product__collection__slug="hoodie")
                )).distinct().order_by('-pub_date', '-sort_order').defer(
                    'id', 'is_active', 'sort_order', 'product_id',
                    'product__is_active', 'product__pub_date',
                )[:6]
        return super().dispatch(request, *args, **kwargs)


class CollectionsMixin(View):

    def dispatch(self, request, *args, **kwargs):
        self.collections = Collection.objects.filter(is_active=True).order_by('-sort_order')
        return super().dispatch(request, *args, **kwargs)


class SEOMixin(View):

    def dispatch(self, request, *args, **kwargs):
        current_path = str(request.path)
        if current_path.startswith("/ru/"):
            pass
        elif current_path.startswith("/en/"):
            current_path = "/ru/" + current_path[4:]
        else:
            current_path = "/ru/" + current_path[1:]

        self.main_path = settings.BASE_URL + current_path
        return super().dispatch(request, *args, **kwargs)


class CatalogMixin(View):

    def dispatch(self, request, *args, **kwargs):
        self.catalog_slug = kwargs.get('catalog_slug')

        catalog_filters = Q(is_active=True) & Q(product__is_active=True) &  \
                Q(product__collection__is_active=True) &  \
                Q(images__is_active=True)

        self.collection = None
        if self.catalog_slug is not None:
            self.collection = Collection.objects.filter(slug=self.catalog_slug).first()
            if self.collection is not None:
                catalog_filters = catalog_filters & Q(product__collection=self.collection)

        catalog_filters = catalog_filters & (
            (Q(product__collection__slug="hoodie") & Q(variation__id=2)) |  \
            ~Q(product__collection__slug="hoodie")
        )

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

    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
        if self.products_in_cart.count() == 0:
            return HttpResponseRedirect(reverse('cart'))

        BUYING_TYPE_DELIVERY = 'DELIVERY'
        BUYING_TYPE_SELF = 'SELF'
        self.order = Order.objects.filter(id=self.cart.order_id).first()
        use_old_order_data = False
        self.firstName = request.POST.get('firstName')
        self.lastName = request.POST.get('lastName')
        self.email = request.POST.get('email')
        self.phone = request.POST.get('phone')
        self.payment = request.POST.get('payment')
        self.delivery_type = request.POST.get('delivery_type')  # тип доставки
        self.chosenPost = request.POST.get('chosenPost')  # номер поста
        self.cityPost = request.POST.get('city')  # город
        self.order_comment = request.POST.get('order_comment')  # комментарий

        if self.order_comment is None:
            self.order_comment = ""
        if self.delivery_type is None:
            if self.order is None:
                return HttpResponseRedirect(reverse('checkout'))
            else:
                use_old_order_data = True

        _buying_type = "DELIVERY"
        if self.delivery_type == "pickup":
            self.addresPost = request.POST.get('addresPost')  # адрес
            _buying_type = BUYING_TYPE_SELF
        else:
            self.addresPost = request.POST.get('addresPost-show')  # адрес
            _buying_type = BUYING_TYPE_DELIVERY

        self.timePost = request.POST.get('timePost')  # приблизительное время доставки
        self.pricePost = request.POST.get('pricePost')  # стоимость доставки
        if self.cart.promocode is not None:
            if self.cart.promocode.free_delivery == True:
                self.pricePost = 0

        required_params_list = [
            self.firstName, self.lastName, self.email, self.phone,
            self.payment, self.delivery_type, self.cityPost,
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
            self.cityPost = self.order.city  # город
            self.addresPost = self.order.address  # адрес
            self.pricePost = self.order.delivery_price  # стоимость доставки
            self.timePost = '7 - 14'  # приблизительное время доставки
            self.order_comment = self.order.comment
        else:
            self.order, _ = Order.objects.get_or_create(
                first_name=self.firstName, last_name=self.lastName, email=self.email,
                phone=self.phone, city=self.cityPost, address=self.addresPost, buying_type=_buying_type,
                paid=False, 
            )
            self.order.comment=self.order_comment
            self.order.total_products=self.cart.total_products
            self.order.price_before_discount=self.cart.price_before_discount
            self.order.final_price=self.cart.final_price
            self.order.delivery_price = int(self.pricePost)
            self.order.cart_id = self.cart.id
            self.order.save()

            for product_in_order in self.cart.products.all():
                subtotal_price_before_discount = product_in_order.subtotal_price_before_discount
                if product_in_order.subtotal_price_before_discount is None:
                    subtotal_price_before_discount = product_in_order.subtotal_price
                OrderProduct.objects.create(
                    order=self.order,
                    name=product_in_order.get_receipt_name(),
                    qty=product_in_order.qty,
                    subtotal_price=product_in_order.subtotal_price,
                    subtotal_price_before_discount=subtotal_price_before_discount,
                )
            self.cart.order_id = self.order.id
            self.cart.save()

        return super().dispatch(request, *args, **kwargs)


class OrderMixin(View):

    def dispatch(self, request, *args, **kwargs):
        self.order = Order.objects.filter(id=self.cart.order_id).first()
        if self.order is None:
            return HttpResponseRedirect(reverse('checkout'))
        # self.cart.save()
        # self.order.save()

        return super().dispatch(request, *args, **kwargs)


class SuccessMixin(View):

    @transaction.atomic
    def dispatch(self, request, *args, **kwargs):
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


def calculate_signature(*args) -> str:
    """Create signature MD5.
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


class PodeliMixin(View):

    def dispatch(self, request, *args, **kwargs):
        try:
            self.podeli_amount = int(self.cart.final_price) + int(self.pricePost)
            self.signature = calculate_signature('KIRUMI', f'{ self.podeli_amount }.00', 0, settings.ROBOKASSA_PASS1)
        except AttributeError:
            self.podeli_amount = int(self.cart.final_price)
        self.podeli_is_available = False
        if self.podeli_amount > 300 and self.podeli_amount < 15000:
            self.podeli_is_available = True

        return super().dispatch(request, *args, **kwargs)
