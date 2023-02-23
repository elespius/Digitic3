# Generated by Django 3.2.12 on 2022-02-15 14:18

from django.conf import settings
from django.db import migrations
from django.db.models import Count

USER_ADDRESS_LIMIT = settings.MAX_USER_ADDRESSES


def clear_addresses(apps, schema_editor):
    User = apps.get_model("account", "User")
    Address = apps.get_model("account", "Address")

    users = User.objects.annotate(address_count=Count("addresses")).filter(
        address_count__gt=USER_ADDRESS_LIMIT
    )
    address_pks_to_delete = set()

    for user in users.iterator():
        user_default_addresses_ids = [
            user.default_billing_address_id,
            user.default_shipping_address_id,
        ]
        address_pks_to_delete.update(
            user.addresses.exclude(id__in=user_default_addresses_ids)
            .order_by("pk")[: user.address_count - USER_ADDRESS_LIMIT]
            .values_list("id", flat=True)
        )

    Address.objects.filter(pk__in=address_pks_to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0056_merge_20210903_0640"),
    ]

    operations = [
        migrations.RunPython(clear_addresses, migrations.RunPython.noop),
    ]
