# Generated by Django 3.2.18 on 2023-02-28 11:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0041_add_calculation_transaction_events"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transactionevent",
            name="type",
            field=models.CharField(
                choices=[
                    ("authorization_success", "Represents success authorization"),
                    ("authorization_failure", "Represents failure authorization"),
                    ("authorization_adjustment", "Represents authorization adjustment"),
                    ("authorization_request", "Represents authorization request"),
                    ("charge_success", "Represents success charge"),
                    ("charge_failure", "Represents failure charge"),
                    ("charge_back", "Represents chargeback."),
                    ("charge_request", "Represents charge request"),
                    ("refund_success", "Represents success refund"),
                    ("refund_failure", "Represents failure refund"),
                    ("refund_reverse", "Represents reverse refund"),
                    ("refund_request", "Represents refund request"),
                    ("cancel_success", "Represents success cancel"),
                    ("cancel_failure", "Represents failure cancel"),
                    ("cancel_request", "Represents cancel request"),
                    ("info", "Represents an info event"),
                ],
                default="info",
                max_length=128,
            ),
        ),
    ]
