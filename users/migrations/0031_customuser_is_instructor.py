
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0030_alter_banktransaction_unique_together_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_instructor",
            field=models.BooleanField(
                default=False,
                verbose_name="Instructor",
                help_text=(
                    "Instructors can manage machine access for members."
                ),
            ),
        ),
    ]
