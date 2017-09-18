# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-15 13:53
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.postgres.fields.hstore
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product', '0033_auto_20170227_0757'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Wishlist',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('public', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='WishlistItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attributes', django.contrib.postgres.fields.hstore.HStoreField(default={})),
                ('watch', models.BooleanField(default=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.Product')),
                ('variant_object', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='product.ProductVariant')),
                ('wishlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wishlist.Wishlist')),
            ],
        ),
        migrations.CreateModel(
            name='WishlistNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product.ProductVariant')),
                ('wishlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='wishlist.Wishlist')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='wishlistnotification',
            unique_together=set([('wishlist', 'variant')]),
        ),
        migrations.AlterUniqueTogether(
            name='wishlistitem',
            unique_together=set([('wishlist', 'product', 'variant_object', 'attributes')]),
        ),
    ]
