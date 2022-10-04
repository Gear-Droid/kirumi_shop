from dadata import Dadata

from django.shortcuts import render
from django.urls import reverse
from django.http import (
    HttpResponse, JsonResponse, HttpResponseNotFound, HttpResponseRedirect,
)
from django.db import IntegrityError
from django.db.models import Q
from django.contrib import messages
from django.views import View
from django.views.decorators.cache import cache_page
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .models import (
    Banner,
    ColoredProduct,
    CartProduct,
    Promocode,
)
from .mixins import (
    CartMixin,
    CartProductMixin,
    NewProductsMixin,
    CollectionsMixin,
    CatalogMixin,
    PaymentMixin,
    OrderMixin,
    CachedCitiesMixin,
)


class BasePageView(CartMixin, CollectionsMixin):
    pass


class HomePageView(BasePageView, NewProductsMixin):

    def get(self, request, *args, **kwargs):
        self.banners = Banner.objects.filter(is_active=True).order_by('-sort_order')

        context = {
            'meta':{
                'Title': "Онлайн-магазин аниме-одежды Kirumi",
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
                'Title': "Онлайн-магазин аниме-одежды Kirumi",
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
                'Title': str(colored_product),
                'keywords': colored_product.product.description,
                'page_description': colored_product.product.description,
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
                'Title': "О бренде Kirumi",
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
            },
            'collections': self.collections,
            'cart': self.cart,
            'colored_products': self.new_products,
        }
        return render(request, 'new/new.html', context=context)


class CatalogView(BasePageView, CatalogMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Каталог аниме-одежды Kirumi",
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


class CheckoutView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        if self.products_in_cart.count() == 0:
            return HttpResponseRedirect(reverse('cart'))

        context = {
            'meta':{
                'Title': "Детали заказа",
            },
            'collections': self.collections,
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
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


class PaymentView(BasePageView, CartProductMixin, PaymentMixin):

    def post(self, request, *args, **kwargs):

        context = {
            'meta': {
                'Title': 'Оплата заказа',
            },
            'delivery_details':{
                'chosenPost': self.chosenPost,
                'addresPost': self.addresPost,
                'pricePost': self.pricePost,
                'timePost': self.timePost,
            },
            'order_details':{
                'firstName': self.firstName,
                'lastName': self.lastName,
                'email': self.email,
                'phone': self.phone,
            },
            'collections': self.collections,
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
        }
        return render(request, 'cart/checkout/payment/payment.html', context=context)


class SuccessView(BasePageView, OrderMixin):

    @xframe_options_sameorigin
    def get(self, request, *args, **kwargs):
        context = {
            'meta': {
                'Title': 'Успешная оплата',
            },
            'cart': self.cart,
        }
        return render(request, 'cart/checkout/payment/success/success.html', context=context)


class TermsOfUseView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Пользовательское соглашение",
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
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'public_offer/public_offer.html', context=context)


class ContactsView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Контакты",
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
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'delivery_and_payment/delivery_and_payment.html', context=context)


class CitiesAPIView(CachedCitiesMixin, View):

    def get(self, request, *args, **kwargs):
        contains_param = request.GET.get("contains")
        if contains_param is None:
            return HttpResponseNotFound()

        self.result_list = tuple([
            x for x in self.cities_dict.items()  \
            if str(x[1]).lower().__contains__(str(contains_param).lower())
        ])[:7]
        if len(self.result_list) < 1:
            return JsonResponse(
                { "status": "EMPTY", "cities": self.result_list },
                json_dumps_params = dict(ensure_ascii=False),
            )

        return JsonResponse(
            { "status": "OK", "cities": self.result_list },
            json_dumps_params = dict(ensure_ascii=False),
        )


class AddressesAPIView(CachedCitiesMixin, View):

    def get(self, request, *args, **kwargs):
        token = "5dd895d684d4d5d9cbca342c1880c7684916e3c9"
        secret = "9d0a5b6bd16930cd0b05ab90eb8e802aeccc6f22"
        city_code_param = request.GET.get("city_code")
        contains_param = request.GET.get("contains")

        if city_code_param is None or contains_param is None:
            return HttpResponseNotFound()
        city = self.cities_dict.get(city_code_param)
        if city is None:
            return JsonResponse(
                { "status": "ERROR", "details": "wrong city_code" },
                json_dumps_params = dict(ensure_ascii=False),
            )

        dadata = Dadata(token, secret)
        addresses_result = []
        if len(contains_param) < 3:
            return JsonResponse(
                { "status": "EMPTY", "city": city, "addresses": addresses_result },
                json_dumps_params = dict(ensure_ascii=False),
            )
        addresses_result = dadata.suggest("address", f"{city} {contains_param}")
        addresses_value_list = list([ x.get("value") for x in addresses_result ])
        filtered_addresses_value_list = list(filter(lambda x : str(x).startswith(city), addresses_value_list))
        cleared_addresses_list = list(map(lambda x: x[len(city)+2:], filtered_addresses_value_list))[:7]

        return JsonResponse(
            { "status": "OK", "city": city, "addresses": cleared_addresses_list },
            json_dumps_params = dict(ensure_ascii=False),
        )
