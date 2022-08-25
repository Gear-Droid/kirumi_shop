# Generated by Django 4.0.4 on 2022-05-17 21:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainapp', '0004_coloredproduct_name_en_coloredproduct_name_ru'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cart',
            options={'ordering': ['-created'], 'verbose_name': 'Корзина', 'verbose_name_plural': 'Корзины'},
        ),
        migrations.AlterModelOptions(
            name='cartproduct',
            options={'verbose_name': 'Продукт в корзине', 'verbose_name_plural': 'Продукты в корзине'},
        ),
        migrations.AlterModelOptions(
            name='collection',
            options={'verbose_name': 'Коллекция', 'verbose_name_plural': 'Коллекции'},
        ),
        migrations.AlterModelOptions(
            name='coloredproduct',
            options={'verbose_name': 'Продукт с цветом и изображением', 'verbose_name_plural': 'Продукты с цветом и изображением'},
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': 'Заказ', 'verbose_name_plural': 'Заказы'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'verbose_name': 'Продукт', 'verbose_name_plural': 'Продукты'},
        ),
        migrations.AlterModelOptions(
            name='productimage',
            options={'ordering': ['-sort_order'], 'verbose_name': 'Изображение продукта', 'verbose_name_plural': 'Изображения продукта'},
        ),
        migrations.AlterModelOptions(
            name='promocode',
            options={'verbose_name': 'Промокод', 'verbose_name_plural': 'Промокоды'},
        ),
        migrations.AlterModelOptions(
            name='size',
            options={'verbose_name': 'Размер', 'verbose_name_plural': 'Размеры'},
        ),
        migrations.AlterField(
            model_name='cart',
            name='owner',
            field=models.GenericIPAddressField(protocol='IPv4', unique=True, verbose_name='IP владельца корзины'),
        ),
    ]
