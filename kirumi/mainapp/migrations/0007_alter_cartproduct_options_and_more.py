# Generated by Django 4.0.4 on 2022-09-02 22:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0006_collection_parent'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cartproduct',
            options={'verbose_name': 'Товар в корзине', 'verbose_name_plural': 'Товары в корзине'},
        ),
        migrations.AlterModelOptions(
            name='coloredproduct',
            options={'verbose_name': 'Карточка товара', 'verbose_name_plural': 'Карточки товаров'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'verbose_name': 'Товар', 'verbose_name_plural': 'Товары'},
        ),
        migrations.AlterModelOptions(
            name='productimage',
            options={'ordering': ['-sort_order'], 'verbose_name': 'Изображение товара', 'verbose_name_plural': 'Изображения товара'},
        ),
        migrations.AlterField(
            model_name='cartproduct',
            name='colored_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart_products', to='mainapp.coloredproduct', verbose_name='Карточка товара'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='parent',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='mainapp.collection', verbose_name='Родительская коллекция'),
        ),
        migrations.AlterField(
            model_name='collection',
            name='slug',
            field=models.SlugField(max_length=64, unique=True, verbose_name='Уникальное обозначение'),
        ),
        migrations.AlterField(
            model_name='coloredproduct',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='colors', to='mainapp.product', verbose_name='Базовый товар'),
        ),
        migrations.AlterField(
            model_name='coloredproduct',
            name='slug',
            field=models.SlugField(max_length=64, verbose_name='Уникальное обозначение товара'),
        ),
        migrations.RemoveField(
            model_name='product',
            name='collection',
        ),
        migrations.AddField(
            model_name='product',
            name='collection',
            field=models.ManyToManyField(related_name='products', to='mainapp.collection', verbose_name='Коллекция'),
        ),
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=models.SlugField(max_length=64, unique=True, verbose_name='Уникальное обозначение'),
        ),
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.ImageField(upload_to='product_images/%Y/%m', verbose_name='Изображение товара'),
        ),
    ]
