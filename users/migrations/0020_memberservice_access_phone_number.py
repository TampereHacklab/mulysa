# Generated by Django 3.0.7 on 2020-07-16 10:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_auto_20200616_1207'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberservice',
            name='access_phone_number',
            field=models.CharField(blank=True, help_text='Phone number that can be used to use this memberservice', max_length=20, null=True),
        ),
    ]
