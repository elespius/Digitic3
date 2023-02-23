# Generated by Django 3.2.15 on 2022-09-22 09:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0037_alter_transaction_error"),
    ]

    operations = [
        migrations.AddField(
            model_name="transactionevent",
            name="currency",
            field=models.CharField(blank=True, max_length=3),
        ),
        migrations.AlterField(
            model_name="transactionitem",
            name="reference",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name="transactionevent",
            name="reference",
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name="transactionitem",
            name="type",
            field=models.CharField(blank=True, default="", max_length=512, null=True),
        ),
        migrations.AlterField(
            model_name="transactionevent",
            name="name",
            field=models.CharField(blank=True, default="", max_length=512, null=True),
        ),
    ]
