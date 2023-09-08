# Generated by Django 3.2.20 on 2023-08-21 07:30

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("discount", "0046_move_codes_to_new_model"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="voucher",
            options={"ordering": ("name", "pk")},
        ),
        migrations.RemoveField(
            model_name="voucher",
            name="code",
        ),
        migrations.RemoveField(
            model_name="voucher",
            name="used",
        ),
        migrations.RemoveField(
            model_name="voucher",
            name="usage_limit",
        ),
    ]
