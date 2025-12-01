# Migration: add access_permissions M2M to CustomUser
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ("users", "0030_alter_banktransaction_unique_together_and_more"),
        ("api", "0009_add_accesspermission"),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='access_permissions',
            field=models.ManyToManyField(blank=True, help_text='Access permissions granted to the user, e.g. machine trainings', to='api.AccessPermission'),
        ),
    ]
