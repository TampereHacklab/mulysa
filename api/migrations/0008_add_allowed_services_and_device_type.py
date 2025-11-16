# Generated migration to add allowed_services M2M and device_type field
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("api", "0007_deviceaccesslogentry_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="accessdevice",
            name="device_type",
            field=models.CharField(default="door", max_length=32, choices=[('door', 'Door'), ('machine', 'Machine'), ('other', 'Other')]),
        ),
        migrations.AddField(
            model_name="accessdevice",
            name="allowed_services",
            field=models.ManyToManyField(blank=True, help_text='Services that grant access via this device (leave empty for default)', to="users.MemberService"),
        ),
    ]
