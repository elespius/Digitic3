# Generated by Django 3.2.19 on 2023-06-26 07:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0171_auto_20230518_0854"),
    ]

    operations = [
        migrations.AddField(
            model_name="ordergrantedrefundline",
            name="reason",
            field=models.TextField(blank=True, null=True, default=""),
        ),
    ]
