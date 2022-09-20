from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.db import IntegrityError
from django.db.models import Q
from django.contrib import messages

from .models import (
    Banner,
    ColoredProduct,
    CartProduct,
    Collection
)
from .mixins import (
    CartMixin,
    CartProductMixin,
    NewProductsMixin,
    CollectionsMixin,
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
            'new_products': self.new_products,
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
            'new_products': self.new_products,
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
            'new_products': self.new_products,
        }
        return render(request, 'new/new.html', context=context)


class CatalogView(BasePageView, NewProductsMixin):

    def get(self, request, *args, **kwargs):


        context = {
            'meta':{
                'Title': "Каталог аниме-одежды Kirumi",
            },
            'collections': self.collections,
            'cart': self.cart,
            'new_products': self.new_products,
        }
        return render(request, 'catalog/catalog.html', context=context)


class CartView(BasePageView, CartProductMixin):

    def get(self, request, *args, **kwargs):

        context = {
            'meta':{
                'Title': "Ваша корзина покупок Kirumi",
            },
            'collections': self.collections,
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
        }
        return render(request, 'cart/cart.html', context=context)


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


class CheckoutView(CartProductMixin, BasePageView):

    def get(self, request, *args, **kwargs):
        if self.products_in_cart.count() == 0:
            return HttpResponseRedirect(reverse('cart'))

        for product in self.products_in_cart:
            product.save()
        self.cart.save()

        context = {
            'meta':{
                'Title': "Детали заказа",
            },
            'collections': self.collections,
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
        }
        return render(request, 'cart/checkout/checkout.html', context=context)


class DeliveryWidgetView(CartProductMixin, BasePageView):

    def get(self, request, *args, **kwargs):
        select_series = request.GET.getlist('select_series', [])
        # print(request.GET.get('country_selector', None))
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


class PaymentView(CartProductMixin, BasePageView):

    def post(self, request, *args, **kwargs):
        chosenPost = request.POST.get('chosenPost')     # номер поста
        addresPost = request.POST.get('addresPost')     # адрес
        pricePost = request.POST.get('pricePost')       # стоимость доставки
        timePost = request.POST.get('timePost')         # приблизительное время доставки
        email = request.POST.get('email')               # приблизительное время доставки
        html = f"""
        <html>
            <body>
                chosenPost: {chosenPost} <br>
                addresPost: {addresPost} <br>
                pricePost: {pricePost} <br>
                timePost: {timePost} <br>
                email: {email} <br>
            </body>
        </html>
        """
        context = {
            'meta': {
                'Title': 'Оплата заказа',
            },
            'delivery_details':{
                'chosenPost': chosenPost,
                'addresPost': addresPost,
                'pricePost': pricePost,
                'timePost': timePost,
            },
            'collections': self.collections,
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
        }
        return render(request, 'cart/checkout/payment/payment.html', context=context)


class TermsOfUseView(CartProductMixin, BasePageView):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Пользовательское соглашение",
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'terms_of_use/terms_of_use.html', context=context)


class PublicOfferView(CartProductMixin, BasePageView):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Публичная офферта",
            },
            'collections': self.collections,
            'cart': self.cart,
        }
        return render(request, 'public_offer/public_offer.html', context=context)


class ContactsView(CartProductMixin, BasePageView):

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
