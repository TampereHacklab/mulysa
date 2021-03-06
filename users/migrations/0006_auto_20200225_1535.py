# Generated by Django 3.0.3 on 2020-02-25 15:35

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_auto_20200224_2028"),
    ]

    operations = [
        migrations.AddField(
            model_name="custominvoice",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
                help_text="Automatically set to now when invoice is created",
                verbose_name="Invoice creation date",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="custominvoice",
            name="last_modified",
            field=models.DateTimeField(
                auto_now=True,
                help_text="Last time this invoice was modified",
                verbose_name="Last modified datetime",
            ),
        ),
    ]
