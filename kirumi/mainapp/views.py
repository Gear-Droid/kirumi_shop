from multiprocessing import context
from tokenize import Name
from django.views.generic import View
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.db.models import Q
from django.db import IntegrityError
from django.contrib import messages

from .models import (
    ColoredProduct,
    CartProduct,
)
from .mixins import (
    CartMixin,
    CartProductMixin,
    NewProductsMixin,
)


class HomePageView(CartMixin, NewProductsMixin):

    def get(self, request, *args, **kwargs):
        # collections = Collection.objects.filter(is_active=True).order_by('-sort_order')

        context = {
            'meta':{
                'Title': "Онлайн-магазин аниме-одежды Kirumi",
            },
            # 'collections': collections,
            'new_products': self.new_products,
        }
        return render(request, 'homepage.html', context=context)


class ProductView(CartMixin):

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

        context = {
            'meta':{
                'Title': str(colored_product),
                'keywords': colored_product.product.description,
                'page_description': colored_product.product.description,
            },
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
            if text_response is not None:
                return HttpResponse("Товар уже добавлен в корзину!")
            return HttpResponseRedirect(reverse('cart'))

        self.cart.save()
        if text_response is not None:
            return HttpResponse("Товар успешно добавлен в корзину!")
        return HttpResponseRedirect(reverse('cart'))


class AboutBrandView(View):

    def get(self, request, *args, **kwargs):

        context = {
            'meta':{
                'Title': "О бренде Kirumi",
            },
        }
        return render(request, 'about_brand/about_brand.html', context=context)


class NewProductsView(CartMixin, NewProductsMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Новинки аниме-одежды Kirumi",
            },
            'new_products': self.new_products,
        }
        return render(request, 'new/new.html', context=context)


class CatalogView(CartMixin, NewProductsMixin):

    def get(self, request, *args, **kwargs):
        context = {
            'meta':{
                'Title': "Новинки аниме-одежды Kirumi",
            },
            'new_products': self.new_products,
        }
        return render(request, 'catalog/catalog.html', context=context)


class CartView(CartMixin, CartProductMixin):

    def get(self, request, *args, **kwargs):

        context = {
            'meta':{
                'Title': "Ваша корзина покупок Kirumi",
            },
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


class CheckoutView(CartMixin, CartProductMixin):

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
            'cart': self.cart,
            'products_in_cart': self.products_in_cart,
        }
        return render(request, 'cart/checkout/checkout.html', context=context)


class DeliveryWidgetView(CartMixin, CartProductMixin):

    def get(self, request, *args, **kwargs):
        select_series = request.GET.getlist('select_series', [])
        print(request.GET.get('country_selector', None))
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

class PaymentView(CartMixin, CartProductMixin):

    def get(self, request, *args, **kwargs):
        html = '<html><body>It is now %s.</body></html>' % 666
        return HttpResponse(html)
