# Generated by Django 2.1.2 on 2018-10-12 16:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("product", "0075_auto_20181010_0842")]

    operations = [
        migrations.AlterField(
            model_name="attributevalue",
            name="value",
            field=models.CharField(blank=True, default="", max_length=100),
        )
    ]
