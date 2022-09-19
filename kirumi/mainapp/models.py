from decimal import Decimal

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


WrongResolutionMessage = 'Разрешение изображения не равно {}x{}!'
class WrongResolutionErrorException(Exception):
    pass


class BasicIsActiveAndDateModel(models.Model):

    class Meta:
        abstract = True

    is_active = models.BooleanField(default=True, verbose_name='Активно?')
    pub_date = models.DateField(default=timezone.datetime.today, verbose_name='Дата публикации')


class KirumiBasicSlugNameModel(models.Model):

    class Meta:
        abstract = True

    name = models.CharField(max_length=64, verbose_name='Наименование')
    slug = models.SlugField(max_length=64, unique=True, verbose_name='Уникальное обозначение')

    # def get_absolute_url(self):
    #     return reverse("category_detail", kwargs={"slug": self.slug})


class BasicSortOrderModel(models.Model):

    class Meta:
        abstract = True
        ordering = ['-sort_order']

    sort_order = models.PositiveIntegerField(
        unique=True, verbose_name='Порядок сортировки',
    )


class Banner(BasicIsActiveAndDateModel, BasicSortOrderModel):

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'

    header = models.CharField(max_length=64, verbose_name='Заголовок')
    description = models.TextField(max_length=128, verbose_name='Описание')
    link = models.TextField(max_length=128, verbose_name='Ссылка')
    image = models.ImageField(upload_to="banner_image/%Y/%m", verbose_name='Изображение баннера')


class Collection(BasicIsActiveAndDateModel, KirumiBasicSlugNameModel, BasicSortOrderModel):

    class Meta:
        verbose_name = 'Коллекция'
        verbose_name_plural = 'Коллекции'

    IMG_WIDTH = 500
    IMG_HEIGHT = 700
    IMG_WIDTH_SCALED = 250
    IMG_HEIGHT_SCALED = 350

    parent = models.ForeignKey(
        'self', null=True, blank=True, default=None,
        on_delete=models.CASCADE, verbose_name='Родительская коллекция'
    )
    description = models.TextField(max_length=128, verbose_name='Описание')
    image = models.ImageField(upload_to="collection_image/%Y/%m", verbose_name='Изображение коллекции')

    def __str__(self):
        return self.name

    """ def save(self, *args, **kwargs):
        img = Image.open(self.image)
        if img.width!=self.IMG_WIDTH or img.height!=self.IMG_HEIGHT:
            raise WrongResolutionErrorException(WrongResolutionMessage.format(
                self.IMG_WIDTH, self.IMG_HEIGHT
            ))
        super().save(*args, **kwargs) """


class Size(BasicIsActiveAndDateModel, BasicSortOrderModel):

    class Meta:
        verbose_name = 'Размер'
        verbose_name_plural = 'Размеры'

    size = models.CharField(max_length=64, unique=True, verbose_name='Размер')

    def save(self, *args, **kwargs):
        self.size = self.size.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.size


class Product(BasicIsActiveAndDateModel, KirumiBasicSlugNameModel):

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def allSizes():
        return Size.objects.exclude(size='ONESIZE').filter(is_active=True)

    collection = models.ManyToManyField(
        Collection, verbose_name='Коллекции',
        related_name='products',
    )
    description = models.TextField(max_length=128, verbose_name='Описание')
    sizes = models.ManyToManyField(
        Size, verbose_name='Размеры', default=allSizes
    )

    def __str__(self):
        return self.name


class ProductVariation(BasicIsActiveAndDateModel, KirumiBasicSlugNameModel, BasicSortOrderModel):

    class Meta:
        verbose_name = 'Вариация товара'
        verbose_name_plural = 'Вариации товара'

    name = models.CharField(max_length=256, verbose_name='Наименование вариации', )
    description = models.TextField(
        max_length=512, verbose_name='Описание вариации товара', null=True, blank=True
    )

    def __str__(self):
        return self.name


class ColoredProduct(BasicIsActiveAndDateModel, KirumiBasicSlugNameModel, BasicSortOrderModel):

    class Meta:
        verbose_name = 'Карточка товара'
        verbose_name_plural = 'Карточки товаров'
        unique_together = (('product', 'sort_order'), ('product', 'slug'))

    slug = models.SlugField(max_length=64, unique=False, verbose_name='Уникальное обозначение карточки')
    sort_order = models.PositiveIntegerField(verbose_name='Порядок сортировки')
    product = models.ForeignKey(
        Product, verbose_name='Базовый товар', on_delete=models.CASCADE,
        related_name='colors',
    )
    name = models.CharField(max_length=64, verbose_name='Название цвета', )
    variation = models.ForeignKey(
        ProductVariation, verbose_name='Вариация', on_delete=models.CASCADE,
        related_name='variations', null=True, blank=True
    )
    color_hex_code = models.CharField(max_length=6, verbose_name='Hex code цвета товара (после #)', )
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Актуальная цена', )
    old_price = models.DecimalField(
        null=True, blank=True, max_digits=8, decimal_places=2, verbose_name='Устаревшая цена',
    )

    def get_two_first_images(self):
        return [im for im in self.images.all() if im.is_active==True][:2]


    def __str__(self):
        return "{} - {}".format(self.product, self.name)


class ProductImage(BasicIsActiveAndDateModel, BasicSortOrderModel):

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товара'
        unique_together = (('product_color', 'sort_order'), )
        ordering = ['-sort_order']

    IMG_WIDTH = 500
    IMG_HEIGHT = 700
    IMG_WIDTH_SCALED = 500
    IMG_HEIGHT_SCALED = 700

    sort_order = models.PositiveIntegerField(verbose_name='Порядок сортировки')
    product_color = models.ForeignKey(
        ColoredProduct, verbose_name='Product color', on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(upload_to="product_images/%Y/%m", verbose_name='Изображение товара')
    description = models.CharField(unique=True, max_length=190, verbose_name='Описание')

    def __str__(self):
        return f"{self.product_color.product.name}-{self.product_color.name}-{self.pk}"

    """ def save(self, *args, **kwargs):
        img = Image.open(self.image)
        if img.width!=self.IMG_WIDTH or img.height!=self.IMG_HEIGHT:
            raise WrongResolutionErrorException(
                WrongResolutionMessage.format(self.IMG_WIDTH, self.IMG_HEIGHT)
            )
        super().save(*args, **kwargs) """


class Promocode(BasicIsActiveAndDateModel, BasicSortOrderModel):

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'

    promocode = models.CharField(max_length=16, unique=True, verbose_name='Промокод')

    def __str__(self):
        return f"{self.promocode}"

    def save(self, *args, **kwargs):
        self.promocode = self.promocode.upper()
        super().save(*args, **kwargs)


class Cart(models.Model):

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        unique_together = (('owner', 'created'), )
        ordering = ['-created']

    owner = models.GenericIPAddressField(protocol='IPv4', unique=True, verbose_name='IP владельца корзины')
    created = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания')
    colored_products = models.ManyToManyField(
        ColoredProduct, through='CartProduct'
    )
    total_products = models.PositiveIntegerField(default=0, verbose_name='Общее число товаров в корзине')
    final_price = models.DecimalField(
        max_digits=9, decimal_places=2, default=0, verbose_name='Итоговая цена')

    def save(self, *args, **kwargs):
        self.final_price = 0
        self.total_products = 0
        cart_products = CartProduct.objects.filter(cart=self).all()
        for cart_product in cart_products:
            self.final_price += Decimal(cart_product.subtotal_price)
            self.total_products += int(cart_product.qty)
        super().save(*args, **kwargs)

    def __str__(self):
        return str(f'Корзина ID: {self.id}')


class CartProduct(models.Model):

    class Meta:
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        unique_together = (('cart', 'colored_product', 'size'), )

    # user id field
    cart = models.ForeignKey(
        Cart, verbose_name='Корзина', on_delete=models.CASCADE
    )
    colored_product = models.ForeignKey(
        ColoredProduct, verbose_name='Карточка товара', on_delete=models.CASCADE,
        related_name="cart_products"
    )
    size = models.ForeignKey(
        Size, verbose_name="Размер", on_delete=models.CASCADE,
        related_name="cart_products"
    )
    qty = models.PositiveIntegerField(default=1)
    subtotal_price = models.DecimalField(
        max_digits=9, decimal_places=2, verbose_name='Подытоговая сумма')

    def save(self, *args, **kwargs):
        self.subtotal_price = self.colored_product.price * Decimal(self.qty)
        super().save(*args, **kwargs)
        self.cart.save()

    def __str__(self):
        return "Карточка: ({} - {}) для корзины: ({})".format(
            self.colored_product.product.name, self.colored_product.name, self.cart)


class Order(models.Model):

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    STATUS_NEW = 'NEW'
    STATUS_IN_PROGRESS = 'IN PROGRESS'
    STATUS_READY = 'IS READY'
    STATUS_COMPLETED = 'COMPLETED'

    BUYING_TYPE_SELF = 'SELF'
    BUYING_TYPE_DELIVERY = 'DELIVERY'

    STATUS_CHOICES = (
        (STATUS_NEW, 'Новый заказ'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_IN_PROGRESS, 'Заказ в обработке'),
        (STATUS_READY, 'Заказ готов'),
        (STATUS_COMPLETED, 'Заказ выполнен'),
    )

    BUYING_TYPE_CHOICES = (
        (BUYING_TYPE_SELF, 'Самовывоз'),
        (BUYING_TYPE_DELIVERY, 'Доставка'),
    )

    first_name = models.CharField(max_length=128, verbose_name='Имя')
    last_name = models.CharField(max_length=128, verbose_name='Фамилия')
    email = models.EmailField(max_length=254, verbose_name='Email')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    # cart = models.ForeignKey(Cart, verbose_name='Корзина', on_delete=models.CASCADE, null=True, blank=True)
    address = models.CharField(max_length=1024, verbose_name='Адрес')
    status = models.CharField(
        max_length=100,
        verbose_name='Статус заказа',
        choices=STATUS_CHOICES,
        default=STATUS_NEW,
    )
    buying_type = models.CharField(
        max_length=100,
        verbose_name='Тип заказа',
        choices=BUYING_TYPE_CHOICES,
        default=BUYING_TYPE_DELIVERY,
    )
    comment = models.TextField(verbose_name='Комментарий к заказу', null=True, blank=True)
    created_at = models.DateTimeField(auto_now=True, verbose_name='Дата создания заказа')
    order_date = models.DateField(verbose_name='Дата полученя заказа', default=timezone.datetime.today)

    def __str__(self):
        return str(self.id)
