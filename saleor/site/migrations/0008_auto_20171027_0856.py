# Generated by Django 1.11.5 on 2017-10-27 13:56
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("site", "0007_auto_20171027_0856"),
    ]

    operations = [
        migrations.AlterField(
            model_name="sitesettings",
            name="site",
            field=models.OneToOneField(
                null=False,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="settings",
                to="sites.Site",
            ),
            preserve_default=False,
        ),
        migrations.RemoveField(model_name="sitesettings", name="domain"),
        migrations.RemoveField(model_name="sitesettings", name="name"),
    ]
