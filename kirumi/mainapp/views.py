import requests
import logging

from dadata import Dadata

from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.http import (
    HttpResponse, JsonResponse, HttpResponseNotFound, HttpResponseRedirect,
)
from django.db import IntegrityError
from django.db.models import Q
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .models import (
    Banner,
    ColoredProduct,
    CartProduct,
    Promocode,
)
from .mixins import *
from mainapp.utils import get_delivery_calculation


error_file_logger = logging.getLogger('django')


class BasePageView(CartMixin, CollectionsMixin, SEOMixin):
    pass


class HomePageView(BasePageView, NewProductsMixin):

    def get(self, request, *args, **kwargs):
        self.banners = Banner.objects.filter(is_active=True).order_by('-sort_order')
        context = {
            'meta':{
                'Title': "KIRUMI - Интернет-магазин аниме-одежды",
                'keywords': "интернет-магазин, аниме, аниме одежда, худи, Kirumi, кируми",
                'page_description': "KIRUMI - молодой бренд, вдохновленный многогранностью аниме. У нас вы найдете худи и футболки с Атака Титанов, HunterxHunter, Клинок, рассекающий демонов, Магическая битва",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
            'colored_products': self.new_products,
            'banners': self.banners,
        }
        return render(request, 'homepage.html', context=context)

    def post(self, request, *args, **kwargs):
        self.banners = Banner.objects.filter(is_active=True).order_by('-sort_order')

        context = {
            'meta':{
                'Title': "KIRUMI - Интернет-магазин аниме-одежды",
                'keywords': "интернет-магазин, аниме, аниме одежда, худи, Kirumi, кируми",
                'page_description': "KIRUMI - молодой бренд, вдохновленный многогранностью аниме. У нас вы найдете худи и футболки с Атака Титанов, HunterxHunter, Клинок, рассекающий демонов, Магическая битва",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
            'colored_products': self.new_products,
            'banners': self.banners,
        }
        return render(request, 'homepage.html', context=context)


class ProductView(BasePageView):

    def get(self, request, *args, **kwargs):

        product_slug, color_slug = kwargs.get('product_slug'), kwargs.get('color_slug')
        colored_product = ColoredProduct.objects.select_related(
            'product').prefetch_related('product__sizes').filter(
                Q(is_active=True) & \
                Q(product__is_active=True) & Q(product__collection__is_active=True) & \
                Q(product__slug=product_slug) & Q(slug=color_slug)
        ).first()

        if colored_product is None:
            return HttpResponseRedirect(reverse('homepage'))

        self.new_products = ColoredProduct.objects.select_related('product')  \
            .prefetch_related('images').prefetch_related('product__sizes').filter(
                Q(is_active=True) & Q(product__is_active=True) &  \
                Q(product__collection__is_active=True) &  \
                Q(images__is_active=True) & Q(product=colored_product.product) &  \
                Q(color_hex_code=colored_product.color_hex_code)
            ).distinct().order_by('-pub_date', '-sort_order').defer(
                'id', 'is_active', 'sort_order', 'product_id',
                'product__is_active', 'product__pub_date',
            )

        context = {
            'meta':{
                'Title': '{} {} - {} {}'.format(
                    colored_product.product.collection.first().name,
                    colored_product.product.name,
                    colored_product.name,
                    colored_product.variation.name,
                ),
                'keywords': 'купить, {}, {}, {}, {}, Kirumi, кируми'.format(
                    colored_product.product.collection.first().name,
                    colored_product.product.name,
                    colored_product.name,
                    colored_product.variation.name,
                ),
                'page_description': colored_product.product.description,
                'main_page': self.main_path,
            },
            'other_variations': self.new_products,
            'collections': self.collections,
            'cart': self.cart,
            'images': colored_product.images.filter(is_active=True),
            'colored_product': colored_product,
        }
        return render(request, 'product/product_page.html', context=context)

    def post(self, request, *args, **kwargs):
        add_to_cart = request.POST.get('add_to_cart')
        text_response = request.POST.get('text_response')
        product_size = request.POST.get('size')

        if add_to_cart is None or product_size is None:
            return HttpResponseRedirect(reverse('cart'))

        product_slug, color_slug = kwargs.get('product_slug'), kwargs.get('color_slug')
        colored_product = ColoredProduct.objects.filter(
            Q(product__slug=product_slug) & Q(slug=color_slug)
        ).filter(
            Q(product__is_active=True) & Q(is_active=True)).first()

        if colored_product is None:
            return HttpResponseNotFound()

        size = colored_product.product.sizes.filter(size__exact=product_size).first()
        if size is None:
            return HttpResponseNotFound()

        try:
            cart_product = CartProduct.objects.create(
                cart=self.cart,
                colored_product=colored_product,
                size=size,
            )
            cart_product.save()
        except IntegrityError as err:
            message = "Товар уже добавлен в корзину!"
            if text_response is not None:
                return HttpResponse(message)
            messages.add_message(request, messages.INFO, message)
            return HttpResponseRedirect(reverse('product_page', args=(product_slug, color_slug, )))

        self.cart.save()
        message = "Товар успешно добавлен в корзину!"
        if text_response is not None:
            return HttpResponse(message)
        messages.add_message(request, messages.INFO, message)
        return HttpResponseRedirect(reverse('product_page', args=(product_slug, color_slug, )))


class AboutBrandView(BasePageView):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'main_page': self.main_path,
            },
            'meta':{
                'Title': "О бренде Kirumi",
                'keywords': "интернет-магазин, аниме, аниме одежда, худи, бренд, Kirumi, кируми",
                'page_description': """Мир аниме – это особая философия, которой следуем мы и хотим поделиться с вами.  \
                    В дизайне нашей одежды отражены различные истории персонажей аниме, у каждого из которых свой неповторимый жизненный путь.  \
                    Это делает каждую вещь по-своему уникальной. Стань частью культуры аниме и найди свой путь вместе с Kirumi!  \
                """,
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'about_brand/about_brand.html', context=context)


class NewProductsView(BasePageView, NewProductsMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Новинки аниме-одежды Kirumi",
                'keywords': "новинки, аниме, аниме одежда, худи, интернет-магазин, Kirumi, кируми",
                'page_description': "Новинки худи и футболки с Атака Титанов, HunterxHunter, Клинок, рассекающий демонов, Магическая битва. Онлайн-магазин Kirumi.",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
            'colored_products': self.new_products,
        }
        return render(request, 'new/new.html', context=context)


class CatalogView(BasePageView, CatalogMixin):

    def get(self, request, *args, **kwargs):
        title = "Каталог Kirumi"
        wear = "Одежда"
        if self.collection is not None:
            title = "{} Kirumi".format(self.collection.name)
            wear = self.collection.name

        context = {
            'meta':{
                'Title': title,
                'keywords': "купить, аниме, {}, каталог, аниме одежда, интернет-магазин, Kirumi, кируми".format(wear),
                'page_description': "Каталог худи и футболки с аниме Атака Титанов, HunterxHunter, Клинок, рассекающий демонов, Магическая битва в онлайн-магазине Kirumi.",
                'main_page': self.main_path,
            },
            'catalog_slug': self.catalog_slug,
            'collections': self.collections,
            'cart': self.cart,
            'colored_products': self.catalog_products,
        }
        return render(request, 'catalog/catalog.html', context=context)


class CartView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        self.cart.save()
        context = {
            'meta':{
                'Title': "Корзина покупок Kirumi",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
        }
        return render(request, 'cart/cart.html', context=context)

    def post(self, request, *args, **kwargs):
        promocode = request.POST.get('promocode')
        if promocode is not None:
            promocode = str(promocode).upper()
            promocode = Promocode.objects.filter(promocode=promocode, is_active=True).first()
            self.cart.promocode=promocode
        return self.get(request, *args, **kwargs)


class DeleteCartProductView(CartMixin, CartProductMixin):

    def post(self, request, *args, **kwargs):
        cart_product_id = request.POST.get('cart_product_id')
        cart_product = self.products_in_cart.filter(id=cart_product_id).first()
        if cart_product is None:
            return HttpResponseNotFound()

        delete = request.POST.get('delete')
        if delete is not None:
            try:
                delete = eval(delete)
            except ValueError:
                return HttpResponseRedirect(reverse('cart'))

            if delete==True:
                cart_product.delete()
                self.cart.save()
                return HttpResponseRedirect(reverse('cart'))

        return HttpResponseRedirect(reverse('cart'))


class ChangeCartProductQtyView(CartMixin, CartProductMixin):

    def post(self, request, *args, **kwargs):
        cart_product_id = request.POST.get('cart_product_id')
        cart_product = self.products_in_cart.filter(id=cart_product_id).first()
        if cart_product is None:
            return HttpResponseNotFound()

        new_qty = request.POST.get('qty')
        try:
            new_qty = int(new_qty)
        except ValueError:
            return HttpResponseRedirect(reverse('cart'))

        if new_qty<30 and new_qty>0:
            cart_product.qty = new_qty
            cart_product.save()

        return HttpResponseRedirect(reverse('cart'))


class CheckoutView(BasePageView, CartProductMixin, PodeliMixin):

    def get(self, request, *args, **kwargs):
        if self.products_in_cart.count() == 0:
            return HttpResponseRedirect(reverse('cart'))

        context = {
            'meta':{
                'Title': "Детали заказа",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
            'base_url': settings.BASE_URL,
            'order_details':{
                'podeli_is_available': self.podeli_is_available,
            }
        }
        return render(request, 'cart/checkout/checkout.html', context=context)


class DeliveryWidgetView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        country_selector = request.GET.get('country_selector', None)
        if country_selector == "":
            html = '<html><body>Пожалуйста, выберите страну!</body></html>'
        elif country_selector == "RU":
            context = {
                'SDEK': True,
            }
            return render(request, 'cart/checkout/delivery_widget/delivery_widget_wrapper.html', context=context)
        else:
            return render(request, 'cart/checkout/delivery_widget/delivery_widget_wrapper.html')

        return HttpResponse(html)


class PaymentView(BasePageView, CartProductMixin, PaymentMixin, PodeliMixin):

    def post(self, request, *args, **kwargs):
        context = {
            'meta': {
                'Title': 'Оплата заказа',
                'main_page': self.main_path,
            },
            'delivery_details':{
                'chosenPost': self.chosenPost,
                'cityPost': self.cityPost,
                'addresPost': self.addresPost,
                'pricePost': self.pricePost,
                'timePost': self.timePost,
                'delivery_type': self.delivery_type,
                'order_comment': self.order_comment,
            },
            'order_details':{
                'firstName': self.firstName,
                'lastName': self.lastName,
                'email': self.email,
                'phone': self.phone,
                'podeli_is_available': self.podeli_is_available,
                'podeli_amount': self.podeli_amount,
                'signature': self.signature,
            },
            'collections': self.collections,
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
            'order_id': self.order.id,
        }
        return render(request, 'cart/checkout/payment/payment.html', context=context)


class SuccessView(BasePageView, OrderMixin, SuccessMixin):

    @xframe_options_sameorigin
    def get(self, request, *args, **kwargs):
        context = {
            'meta': {
                'Title': 'Успешная оплата',
                'main_page': self.main_path,
            },
            'cart': self.cart,
            'order_id': self.order.id,
        }
        return render(request, 'cart/checkout/payment/success/success.html', context=context)


class TermsOfUseView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Пользовательское соглашение",
                'page_description': "Пользовательское соглашение онлайн-магазина Kirumi",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'terms_of_use/terms_of_use.html', context=context)


class PublicOfferView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Публичная офферта",
                'page_description': "Публичная офферта онлайн-магазина Kirumi",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'public_offer/public_offer.html', context=context)


class FAQView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "FAQ",
                'page_description': "FAQ онлайн-магазина Kirumi",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'faq/faq.html', context=context)


class ReturnExchangeView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Возврат-обмен",
                'page_description': "Возврат-обмен онлайн-магазина Kirumi",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'return_exchange/return_exchange.html', context=context)


class ContactsView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Контакты",
                'page_description': "Контакты онлайн-магазина Kirumi",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'contacts/contacts.html', context=context)


class PrivacyPolicyView(BasePageView):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Политика конфиденциальности",
                'page_description': "Политика конфиденциальности онлайн-магазина Kirumi",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'privacy_policy/privacy_policy.html', context=context)


class DeliveryAndPaymentView(BasePageView):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Доставка и оплата",
                'page_description': "Доставка и оплата онлайн-магазина Kirumi",
                'main_page': self.main_path,
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'delivery_and_payment/delivery_and_payment.html', context=context)


class CitiesAPIView(CachedCitiesMixin):

    def get(self, request, *args, **kwargs):
        self.contains_param = request.GET.get("contains")
        if self.contains_param is None:
            return HttpResponseNotFound()

        self.result_list = [
            x for x in sorted(list(self.cities_dict.items())[:], key=lambda x: len(str(x[1]).lower()))  \
            if str(x[1]).lower().__contains__(str(self.contains_param).lower())
        ][:7]

        if len(self.result_list) < 1:
            return JsonResponse(
                { "status": "EMPTY", "cities": self.result_list },
                json_dumps_params = dict(ensure_ascii=False),
            )

        return JsonResponse(
            { "status": "OK", "cities": self.result_list },
            json_dumps_params = dict(ensure_ascii=False),
        )


from django.views.decorators.cache import never_cache
class AddressesAPIView(CachedCitiesMixin):

    # @method_decorator(cache_page(30, cache="address_requests_cache"), name='get')
    @method_decorator(cache_page(60*60*24*7, cache="address_requests_cache"), name='get')
    def get(self, request, *args, **kwargs):
        dadata = Dadata(settings.DADATA_TOKEN, settings.DADATA_SECRET)

        self.city_code_param = request.GET.get("city_code")
        self.contains_param = request.GET.get("contains")

        if self.city_code_param is None or self.contains_param is None:
            return HttpResponseNotFound()
        self.city = self.cities_dict.get(self.city_code_param)
        if self.city is None:
            return JsonResponse(
                { "status": "ERROR", "details": "wrong city_code", "addresses": [] },
                json_dumps_params = dict(ensure_ascii=False),
            )

        addresses_result = []
        if len(self.contains_param) < 3:
            return JsonResponse(
                { "status": "EMPTY", "city": self.city, "addresses": addresses_result },
                json_dumps_params = dict(ensure_ascii=False),
            )
        addresses_result = dadata.suggest("address", f"{self.city} {self.contains_param}")
        addresses_value_list = sorted(list([ x.get("value") for x in addresses_result ]))
        filtered_addresses_value_list = filter(lambda x : str(x).startswith(self.city), addresses_value_list)
        cleared_addresses_list = map(lambda x: x[len(self.city)+2:], filtered_addresses_value_list)
        self.cleared_addresses_list = list(filter(lambda x : len(x)>0, cleared_addresses_list))[:7]

        return JsonResponse(
            { "status": "OK", "city": self.city, "addresses": self.cleared_addresses_list },
            json_dumps_params = dict(ensure_ascii=False),
        )


class SDEKAPIView(View):

    # @method_decorator(cache_page(30, cache="SDEK_requests_cache"), name='get')
    @method_decorator(cache_page(60*60*24*7, cache="SDEK_requests_cache"), name='get')
    def get(self, request, *args, **kwargs):
        self.to_location = request.GET.get("to_location")
        self.hoodie_packages_count = request.GET.get("hoodie_packages_count")
        self.shirt_packages_count = request.GET.get("shirt_packages_count")
        if self.to_location is None or self.hoodie_packages_count is None or  \
            self.shirt_packages_count is None:
            return HttpResponseNotFound()

        try:
            self.hoodie_packages_count = int(self.hoodie_packages_count)
            self.shirt_packages_count = int(self.shirt_packages_count)
        except ValueError:
            return HttpResponseNotFound()
        if (self.hoodie_packages_count + self.shirt_packages_count) < 1:
            return HttpResponseNotFound()

        try:
            delivery_calculation_response = get_delivery_calculation(
                to_location=self.to_location,
                hoodie_packages_count=1,
                shirt_packages_count=0,
                # hoodie_packages_count=self.hoodie_packages_count,
                # shirt_packages_count=self.shirt_packages_count,
            )
        except requests.exceptions.RequestException as error:
            error_file_logger.error('SDEK calculator request fail: {}'.format(error))
            return HttpResponseNotFound()
        if delivery_calculation_response is None:
            return HttpResponseNotFound()
        if delivery_calculation_response.get('errors') is not None:
            return JsonResponse(
                { "status": "ERROR", "details": "can't find address", "errors": delivery_calculation_response.get('errors') },
                json_dumps_params = dict(ensure_ascii=False),
            )

        total_sum = delivery_calculation_response.get("total_sum")
        if total_sum > 500:
            total_sum = 500

        return JsonResponse(
            {
                "status": "OK",
                "total_sum": total_sum,
                "calendar_date":  \
                    f"{ delivery_calculation_response.get('calendar_min') } - { delivery_calculation_response.get('calendar_max') }",
            }, json_dumps_params = dict(ensure_ascii=False),
        )


class OffersAPIView(View):

    def get(self, request, *args, **kwargs):
        colored_product = ColoredProduct.objects.first()

        context = {
            "base_url": settings.BASE_URL,
            "colored_product": colored_product,
        }
        return render(request, 'offers/offers.html', context=context, content_type="text/xml; charset=utf-8")
