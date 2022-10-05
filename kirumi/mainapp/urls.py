"""kirumi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views import *


urlpatterns = [
    path('', HomePageView.as_view(), name='homepage'),
    path('product/<slug:product_slug>/<slug:color_slug>/', ProductView.as_view(), name='product_page'),
    path('about_brand/', AboutBrandView.as_view(), name='about_brand'),
    path('new/', NewProductsView.as_view(), name='new_products'),
    path('catalog/', CatalogView.as_view(), name='catalog'),
    path('catalog/<slug:catalog_slug>/', CatalogView.as_view(), name='catalog'),
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/checkout/', CheckoutView.as_view(), name='checkout'),
    path('cart/<int:cart_product_id>/delete/', DeleteCartProductView.as_view(), name='delete_cart_product'),
    path('cart/<int:cart_product_id>/changeqty/', ChangeCartProductQtyView.as_view(), name='change_qty'),
    path('cart/delivery_widget/', DeliveryWidgetView.as_view(), name='delivery_widget'),
    path('cart/checkout/payment/', PaymentView.as_view(), name='payment'),
    path('cart/checkout/payment/success/', SuccessView.as_view(), name='succes'),
    path('terms_of_use/', TermsOfUseView.as_view(), name='terms_of_use'),
    path('public_offer/', PublicOfferView.as_view(), name='public_offer'),
    path('contacts/', ContactsView.as_view(), name='contacts'),
    path('privacy_policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('delivery_and_payment/', DeliveryAndPaymentView.as_view(), name='delivery_and_payment'),
    # === REST API === #
    path('cities/', CitiesAPIView.as_view(), name='cities'),
    path('addresses/', AddressesAPIView.as_view(), name='addresses'),
    path('sdek/calculator/tariff/', SDEKAPIView.as_view(), name='sdek_calculator_tariff'),
]
