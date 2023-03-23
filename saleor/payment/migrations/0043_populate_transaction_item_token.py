# Generated by Django 3.2.18 on 2023-03-20 12:52

from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from ... import __version__
from .tasks.saleor3_12 import (
    update_transaction_token_field,
    update_transaction_token_field_task,
)


def update_transaction_token_field_migration(apps, _schema_editor):
    TransactionItem = apps.get_model("payment", "TransactionItem")

    def on_migrations_complete(sender=None, **kwargs):
        update_transaction_token_field_task.delay()

    if __version__.startswith("3.12"):
        sender = registry.get_app_config("account")
        post_migrate.connect(on_migrations_complete, weak=False, sender=sender)
    else:
        update_transaction_token_field(transaction_item_class=TransactionItem)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0042_auto_20230320_1252"),
    ]

    operations = [
        migrations.RunPython(
            update_transaction_token_field_migration,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
