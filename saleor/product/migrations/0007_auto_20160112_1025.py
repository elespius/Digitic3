# Generated by Django 1.9.1 on 2016-01-12 16:25

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("product", "0006_product_updated_at")]

    operations = [migrations.RenameModel("FixedProductDiscount", "Discount")]
