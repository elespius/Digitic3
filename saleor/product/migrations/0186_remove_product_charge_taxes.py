# Generated by Django 3.2.19 on 2023-07-12 10:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("product", "0185_unmount_product_charge_taxes"),
    ]

    database_operations = [
        migrations.RunSQL(
            sql="ALTER TABLE product_product DROP COLUMN charge_taxes;",
            reverse_sql=migrations.RunSQL.noop,
        )
    ]

    operations = [
        migrations.SeparateDatabaseAndState(database_operations=database_operations),
    ]
