
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_alter_banktransaction_unique_together_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='memberservice',
            name='required_service',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.SET_NULL,
                related_name='dependent_services',
                to='users.memberservice',
                help_text='If set, this service requires another active service before it can be self-subscribed by users.',
            ),
        ),
    ]
