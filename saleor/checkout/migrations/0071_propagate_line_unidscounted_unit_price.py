# Generated by Django 4.2.15 on 2024-10-23 11:43
from django.db import migrations


# Migration moved to 0072, as scheduled task could cause a deadlock, so we need to run
# it once again.
class Migration(migrations.Migration):
    dependencies = [
        ("tax", "0008_auto_20240122_1353"),
        ("product", "0194_auto_20240620_1404"),
        ("checkout", "0070_checkoutline_undiscounted_unit_price_amount"),
    ]

    operations = []
