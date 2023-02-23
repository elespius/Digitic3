# Generated by Django 4.0.7 on 2022-09-14 13:15

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions
import django_countries.fields
import saleor.core.utils.json_serializer


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("channel", "0005_channel_allocation_strategy"),
    ]

    operations = [
        migrations.CreateModel(
            name="TaxClass",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "private_metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                        null=True,
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                        null=True,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
            ],
            options={
                "ordering": ("name", "pk"),
            },
        ),
        migrations.CreateModel(
            name="TaxConfiguration",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "private_metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                        null=True,
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        encoder=saleor.core.utils.json_serializer.CustomJsonEncoder,
                        null=True,
                    ),
                ),
                ("charge_taxes", models.BooleanField(default=True)),
                (
                    "tax_calculation_strategy",
                    models.CharField(
                        blank=True,
                        choices=[("FLAT_RATES", "Flat rates"), ("TAX_APP", "Tax app")],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("display_gross_prices", models.BooleanField(default=True)),
                ("prices_entered_with_tax", models.BooleanField(default=True)),
                (
                    "channel",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tax_configuration",
                        to="channel.channel",
                    ),
                ),
            ],
            options={
                "ordering": ("pk",),
            },
        ),
        migrations.CreateModel(
            name="TaxClassCountryRate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("country", django_countries.fields.CountryField(max_length=2)),
                ("rate", models.DecimalField(decimal_places=3, max_digits=12)),
                (
                    "tax_class",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="country_rates",
                        to="tax.taxclass",
                    ),
                ),
            ],
            options={
                "ordering": (
                    "country",
                    django.db.models.expressions.OrderBy(
                        django.db.models.expressions.F("tax_class_id"), nulls_first=True
                    ),
                    "pk",
                ),
            },
        ),
        migrations.CreateModel(
            name="TaxConfigurationPerCountry",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("country", django_countries.fields.CountryField(max_length=2)),
                ("charge_taxes", models.BooleanField(default=True)),
                (
                    "tax_calculation_strategy",
                    models.CharField(
                        blank=True,
                        choices=[("FLAT_RATES", "Flat rates"), ("TAX_APP", "Tax app")],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("display_gross_prices", models.BooleanField(default=True)),
                (
                    "tax_configuration",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="country_exceptions",
                        to="tax.taxconfiguration",
                    ),
                ),
            ],
            options={
                "ordering": ("country", "pk"),
                "unique_together": {("tax_configuration", "country")},
            },
        ),
        migrations.AddConstraint(
            model_name="taxclasscountryrate",
            constraint=models.UniqueConstraint(
                fields=("country", "tax_class"), name="unique_country_tax_class"
            ),
        ),
        migrations.AddConstraint(
            model_name="taxclasscountryrate",
            constraint=models.UniqueConstraint(
                condition=models.Q(("tax_class", None)),
                fields=("country",),
                name="unique_country_without_tax_class",
            ),
        ),
    ]
