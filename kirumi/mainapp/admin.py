from .models import *

from django.contrib import admin, messages
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ngettext
from modeltranslation.admin import TranslationAdmin


class BasicIsActiveAndDateAdmin(admin.ModelAdmin):

    date_hierarchy = 'pub_date'
    actions = ('make_active', 'make_disabled', )

    @admin.action(description='Отметить выбранные объекты активными', permissions=['change'])
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, ngettext(
            '%d объект был успешно отмечен активным.',
            '%d объекты были успешно отмечены активными.',
            updated,
        ) % updated, messages.SUCCESS)

    @admin.action(description='Отметить выбранные объекты неактивными', permissions=['change'])
    def make_disabled(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, ngettext(
            '%d объект был успешно отмечен неактивным.',
            '%d объекты были успешно отмечены неактивными.',
            updated,
        ) % updated, messages.SUCCESS)


class BasicSlugAdmin(admin.ModelAdmin):

    # Поле slug будет заполнено на основе поля name
    prepopulated_fields = {"slug": ("name_en", )}
    search_fields = ('name_ru', 'name_en', 'slug', )
    list_display_links = ('slug', )


class BasicSortOrderAdmin(admin.ModelAdmin):

    ordering = ('-sort_order', )
    list_editable = ('sort_order', )

    def get_changeform_initial_data(self, request):
        last_ordered_object = self.model.objects.order_by('-sort_order').first()
        curr_max_sort_order_plus1 = 1
        if last_ordered_object is not None:
            curr_max_sort_order_plus1 = last_ordered_object.sort_order + 1
        return {'sort_order': curr_max_sort_order_plus1}


class BannerAdmin(TranslationAdmin, BasicIsActiveAndDateAdmin, BasicSortOrderAdmin):
    fieldsets = (
        (None, {
            'fields': (
                ('header_ru', 'header_en', 'is_active'),
                ('description_ru', 'description_en'),
                ('link', ),
                ('image', 'get_image'),
                ('pc_image'),
                ('sort_order', 'pub_date'),
            )
        }),
    )
    list_display = (
        'sort_order', 'pub_date', 'header', 'link', 'get_image', 'is_active',
    )
    list_display_links = ('header', )
    readonly_fields = ('pub_date','get_image', )
    list_filter = ('is_active', 'pub_date', )

    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="50" height="70" />')
    get_image.short_description = "Текущее изображение"

    def get_pc_image(self, obj):
        return mark_safe(f'<img src={obj.pc_image.url} width="50" height="70" />')
    get_pc_image.short_description = "Текущее изображение"


class HelloBannerAdmin(BasicIsActiveAndDateAdmin, BasicSortOrderAdmin):
    list_display = (
        'id', 'sort_order', 'pub_date', 'get_image', 'is_active',
    )
    list_display_links = ('id', )

    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="50" height="70" />')
    get_image.short_description = "Текущее изображение"


class CollectionAdmin(TranslationAdmin, BasicIsActiveAndDateAdmin, BasicSlugAdmin, BasicSortOrderAdmin):
    fieldsets = (
        (None, {
            'fields': (
                ('parent', 'name_ru', 'name_en', 'is_active'),
                ('description_ru', 'description_en'),
                ('image', 'get_image'),
                ('sort_order', 'pub_date', 'slug'),
            )
        }),
    )
    list_display = (
        'sort_order', 'pub_date', 'slug', 'name', 'get_image', 'is_active',
    )
    readonly_fields = ('pub_date','get_image', )
    list_filter = ('is_active', 'pub_date', )

    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="50" height="70" />')
    get_image.short_description = "Текущее изображение"



class SizeAdmin(BasicIsActiveAndDateAdmin, BasicSortOrderAdmin):

    fields = (('size', 'is_active'), ('sort_order', 'pub_date'), )
    list_display = ('sort_order', 'pub_date', 'size', 'is_active', )
    list_display_links = ('size', )
    readonly_fields = ('pub_date', )
    list_filter = ('is_active', 'pub_date', )


class GetCurrentColor(object):

    def get_color(self, obj):
        return mark_safe(
            f'<div style="background: #{ obj.color_hex_code }; min-height: 16px; \
                min-width: 28px; max-width: 28px; border: 1px solid; margin: auto;"></div>'
        )
    get_color.short_description = "Изображение цвета"


class ProductImageInline(admin.TabularInline):

    model = ProductImage
    extra = 0

    fields = (
        'sort_order', 'pub_date',
        'image', 'get_current_image',
        'description',
        'is_active',
    )
    readonly_fields = ('pub_date', 'get_current_image', )
    ordering = ('-sort_order', )

    def get_current_image(self, obj):
        return mark_safe(f'<img src={ obj.image.url } width="50" height="70" />')
    get_current_image.short_description = "Изображение"

    """def edit_link(self, instance):
        url = reverse('admin:%s_%s_change' % (
            instance._meta.app_label,  instance._meta.model_name),  args=[instance.pk] )
        if instance.pk:
            return mark_safe(u'<a href="{u}">edit</a>'.format(u=url))
        else:
            return ' - '
    edit_link.short_description = "Edit link"""


class ColoredProductAdmin(BasicIsActiveAndDateAdmin, BasicSlugAdmin, GetCurrentColor):

    class Meta:
        model = ColoredProduct

    fields = (
        ('product', 'status'),
        ('name_ru', 'name_en', 'color_hex_code', 'get_color', 'is_active'),
        ('price', 'old_price'),
        ('sort_order', 'pub_date', 'slug'),
        'variation',
    )
    list_display = (
        'sort_order', 'pub_date', 'product', 'slug',
        'name_ru', 'name_en', 'variation', 'color_hex_code', 'price',
        'old_price', 'is_active',
    )
    list_editable = ('sort_order', )
    list_filter = ('is_active', 'pub_date', )
    search_fields = ('name_ru', 'name_en', 'slug', 'product__name_ru', 'product__name_en')
    readonly_fields = ('product', 'get_color', )
    inlines = [
        ProductImageInline,
    ]

    def save_model(self, request, obj, form, change):
        
        for afile in request.FILES.getlist('multi'):
            product_color_slug = obj.slug
            product_slug = Product.objects.filter(colors=obj).first().slug
            last_prod_img = ProductImage.objects.filter(
                product_color=obj).order_by('-sort_order').first()
            curr_max_sort_order_plus1 = 1
            if last_prod_img is not None:
                curr_max_sort_order_plus1 = last_prod_img.sort_order + 1

            ProductImage.objects.get_or_create(
                product_color=obj, image=afile,
                description="{}-{}-{}".format(
                    product_slug, product_color_slug, curr_max_sort_order_plus1
                ),
                sort_order=curr_max_sort_order_plus1)

        super().save_model(request, obj, form, change)


class ColoredProductInline(admin.TabularInline, GetCurrentColor):
    
    class Media:
        css = {
            'all': ('admin/css/user_changes/columns.css',)
        }

    model = ColoredProduct
    extra = 0

    fields = (
        'sort_order', 'pub_date',
        'name_ru', 'name_en', 'variation', 'color_hex_code', 'get_color',
        'price', 'old_price', 'get_first_image', 'get_second_image',
        'edit_link', 'slug', 'is_active',
    )
    prepopulated_fields = {"slug": ("product", "name_en",)}
    readonly_fields = ('pub_date', 'get_color', 'edit_link', 'get_first_image', 'get_second_image', )
    ordering = ('-sort_order', )

    def get_first_image(self, obj):
        image_model = obj.images.filter(is_active=True, product_color=obj).order_by('-sort_order').first()
        return mark_safe(f'<img src={ image_model.image.url } width="50" height="70" />')
    get_first_image.short_description = "Первое изображение"

    def get_second_image(self, obj):
        image_model = obj.images.filter(is_active=True, product_color=obj).order_by('-sort_order')[1:2].first()
        return mark_safe(f'<img src={ image_model.image.url } width="50" height="70" />')
    get_second_image.short_description = "Второе изображение"

    def edit_link(self, instance):
        url = reverse('admin:%s_%s_change' % (
            instance._meta.app_label,  instance._meta.model_name),  args=[instance.pk] )
        if instance.pk:
            return mark_safe(u'<a href="{u}">Изменить</a>'.format(u=url))
        else:
            return ' - '
    edit_link.short_description = "Ссылка для изменения"


class ProductVariationAdmin(TranslationAdmin, BasicIsActiveAndDateAdmin, BasicSlugAdmin):

    class Meta:
        model = ProductVariation

    fields = (
        ('name_ru', 'name_en', 'is_active'),
        ('description_ru', 'description_en'),
        ('image', 'get_image'),
        ('sort_order', 'pub_date', 'slug'),
    )
    list_editable = ('sort_order', )
    list_display = ('sort_order', 'pub_date', 'slug', 'name_ru', 'name_en', 'get_image', 'is_active', )
    list_filter = ('is_active', 'pub_date', )
    readonly_fields = ('pub_date', 'get_image')

    def get_image(self, obj):
        return mark_safe(f'<img src={obj.image.url} width="50" height="70" />')
    get_image.short_description = "Текущее изображение"


class ProductAdmin(TranslationAdmin, BasicIsActiveAndDateAdmin, BasicSlugAdmin):

    class Meta:
        model = Product

    fields = (
        ('name_ru', 'name_en', 'is_active'),
        ('description_ru', 'description_en'),
        ('collection', 'sizes'),
        ('pub_date', 'slug'),
    )
    list_display = ('pub_date', 'slug', 'name_ru', 'name_en', 'is_active', )
    list_filter = ('is_active', 'pub_date', 'sizes', 'collection', )
    readonly_fields = ('pub_date', )
    inlines = [
        ColoredProductInline,
    ]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            # *** Start Coding for Custom Needs ***
            last = ColoredProduct.objects.order_by('-sort_order').first()
            last_sort_order_plus1 = 1
            if last is not None:
                last_sort_order_plus1 = last.sort_order + 1
            if instance.sort_order is None:
                instance.sort_order = last_sort_order_plus1
            # *** End Coding for Custom Needs ***
            instance.save()
        formset.save_m2m()


class PromocodeAdmin(BasicIsActiveAndDateAdmin, BasicSortOrderAdmin):

    fields = (
        ('promocode', 'is_active', ),
        ('discount', 'free_delivery', ),
        ('sort_order', 'pub_date', ),
    )
    list_display = ('sort_order', 'pub_date', 'promocode', 'discount', 'free_delivery', 'is_active', )
    list_display_links = ('promocode', )
    readonly_fields = ('pub_date', )
    list_filter = ('is_active', 'pub_date', )
    search_fields = ('promocode', )


class CartProductInline(admin.TabularInline, GetCurrentColor):
    
    model = CartProduct
    extra = 0

    fields = (
        'colored_product', 'get_first_image',
        'size', 'qty',
        'subtotal_price_before_discount', 'subtotal_price',
    )
    readonly_fields = (
        'colored_product', 'get_color', 'get_first_image',
        'subtotal_price_before_discount', 'subtotal_price',
    )

    def get_first_image(self, obj):
        image_model = obj.colored_product.images.filter(is_active=True, product_color=obj.colored_product).order_by('-sort_order').first()
        return mark_safe(f'<img src={ image_model.image.url } width="50" height="70" />')
    get_first_image.short_description = "Первое изображение"


class CartAdmin(admin.ModelAdmin):

    class Meta:
        model = Cart

    fields = (
        ('created', 'session_key', ),
        ('owner', 'promocode', ),
        ('total_products', 'price_before_discount', 'final_price'),
        ('paid', 'order_link', ),
    )
    list_display = (
        'created', 'owner', 'promocode', 'total_products',
        'price_before_discount', 'final_price', 'paid', 'order_link',
    )
    readonly_fields = (
        'created', 'session_key', 'owner', 'paid', 'order_id',
        'total_products', 'price_before_discount', 'final_price',
        'order_link',
    )
    list_filter = ('created', 'paid')
    inlines = [
        CartProductInline,
    ]

    def order_link(self, instance):
        url = reverse('admin:%s_%s_change' % (
            instance._meta.app_label, "order"),  args=[instance.order_id] )
        if instance.pk:
            return mark_safe(u'<a href="{u}">{order}</a>'.format(u=url, order=instance.order_id))
        else:
            return ' - '
    order_link.short_description = "Номер заказа"


class CartProductAdmin(admin.ModelAdmin):

    class Meta:
        model = CartProduct


class OrderProductInline(admin.TabularInline):

    model = OrderProduct
    extra = 0

    fields = (
        'order', 'name',
        'qty',
        'subtotal_price',
        'subtotal_price_before_discount',
    )
    readonly_fields = ('order', )


class OrderAdmin(admin.ModelAdmin):

    class Meta:
        model = Order

    fields = (
        ('status', 'get_status', 'created_at', ),
        ('paid_datetime', 'paid'),
        ('last_name', 'first_name', ),
        ('email', 'phone', ),
        ('buying_type', 'city',),
        ('address', 'comment', ),
        ('total_products', ),
        ('final_price', 'price_before_discount', ),
        ('delivery_price', ),
    )
    list_display = (
        'id', 'created_at', 'get_status',
        'paid', 'paid_datetime',
        'last_name', 'first_name',
        'email', 'phone', 'buying_type',
        'city', 'address',
    )
    readonly_fields = (
        'get_status', 'created_at',
    )
    list_filter = ('status', 'paid', 'paid_datetime', )
    search_fields = ('id', 'last_name', 'first_name', 'email', 'phone', )
    inlines = [
        OrderProductInline,
    ]

    def get_status(self, obj):
        status_choice = ""
        for status, value in obj.STATUS_CHOICES:
            if obj.status==status:
                status_choice = value
        color_dict = {
            obj.STATUS_NEW: "red",
            obj.STATUS_IN_PROGRESS: "orange",
            obj.STATUS_CONFIRMED: "blue",
            obj.STATUS_COMPLETED: "green",
        }
        order_color = color_dict.get(obj.status)
        return mark_safe(
            f'<span style="color: { order_color };">{ status_choice }</span>'
        )
    get_status.short_description = "Статус"


admin.site.register(Banner, BannerAdmin)
admin.site.register(HelloBanner, HelloBannerAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Size, SizeAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ColoredProduct, ColoredProductAdmin)
admin.site.register(Promocode, PromocodeAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartProduct, CartProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(ProductVariation, ProductVariationAdmin)
