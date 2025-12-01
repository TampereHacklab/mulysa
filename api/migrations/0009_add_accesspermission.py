# Add AccessPermission model and AccessDevice.allowed_permissions
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("api", "0008_add_allowed_services_and_device_type"),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessPermission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Permission name')),
                ('code', models.SlugField(max_length=100, unique=True, help_text='Short code for the permission')),
                ('education_required', models.BooleanField(default=False, help_text='True if a training/education is required to use targets requiring this permission')),
                ('description', models.TextField(blank=True, default='', help_text='Optional description for this permission')),
            ],
        ),
        migrations.AddField(
            model_name='accessdevice',
            name='allowed_permissions',
            field=models.ManyToManyField(blank=True, help_text='Permissions that grant access via this device (leave empty for default)', to='api.AccessPermission'),
        ),
    ]
