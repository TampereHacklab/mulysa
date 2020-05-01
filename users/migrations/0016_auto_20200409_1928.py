# Generated by Django 3.0.5 on 2020-04-09 19:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0015_auto_20200324_2007"),
    ]

    operations = [
        migrations.AlterField(
            model_name="banktransaction",
            name="archival_reference",
            field=models.CharField(
                max_length=32, unique=True, verbose_name="Archival reference"
            ),
        ),
        migrations.AlterField(
            model_name="servicesubscription",
            name="reminder_sent",
            field=models.DateField(
                blank=True,
                help_text="Set date when a expiration reminder message has been sent to user. Reset to NULL when state changes.",
                null=True,
            ),
        ),
    ]