# Generated by Django 3.0.3 on 2020-03-08 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('users', '0013_auto_20200307_1417'), ('users', '0014_auto_20200308_1414')]

    dependencies = [
        ('users', '0012_nfccard'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nfccard',
            name='cardid',
            field=models.CharField(help_text='Usually hex format', max_length=255, null=True, unique=False, verbose_name='NFC card id number as read by the card reader'),
        ),
        migrations.AlterField(
            model_name='nfccard',
            name='cardid',
            field=models.CharField(help_text='Usually hex format', max_length=512, null=True, unique=True, verbose_name='NFC card id number as read by the card reader'),
        ),
    ]
