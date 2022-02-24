# Generated by Django 3.2.12 on 2022-02-24 14:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0124_alter_order_token"),
        ("discount", "0032_merge_20211109_1210"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderdiscount",
            name="order_token",
            field=models.UUIDField(null=True),
        ),
        migrations.RunSQL(
            """
            UPDATE discount_orderdiscount
            SET order_token = (
                SELECT token
                FROM order_order
                WHERE discount_orderdiscount.order_id = order_order.id
            )
            WHERE order_id IS NOT NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.AlterField(
            model_name="orderdiscount",
            name="order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="discounts",
                to="order.order",
                to_field="number",
            ),
        ),
    ]
