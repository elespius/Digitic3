# Generated by Django 3.2.6 on 2021-11-22 09:28

import django.contrib.postgres.indexes
from django.db import migrations, models

from ...core.search_tasks import set_user_search_document_values


def update_user_search_document_values(apps, _schema_editor):
    User = apps.get_model("account", "User")
    total_count = User.objects.filter(search_document="").count()
    set_user_search_document_values.delay(total_count, 0)


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0056_merge_20210903_0640"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="search_document",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.RemoveIndex(
            model_name="user",
            name="user_search_gin",
        ),
        migrations.AddIndex(
            model_name="user",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["email", "first_name", "last_name"],
                name="order_user_search_gin",
                opclasses=["gin_trgm_ops", "gin_trgm_ops", "gin_trgm_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["search_document"],
                name="user_search_gin",
                opclasses=["gin_trgm_ops"],
            ),
        ),
        migrations.RunPython(
            update_user_search_document_values, reverse_code=migrations.RunPython.noop
        ),
    ]
