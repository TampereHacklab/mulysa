import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import EmailCategory, EmailPreference

logger = logging.getLogger(__name__)

@receiver(post_save, sender=EmailCategory)
def create_preferences_for_new_category(sender, instance, created, **kwargs):
    """
    When a new email category is created, optionally create preferences
    for all existing users based on default_enabled setting
    """
    if created and instance.user_configurable:
        from users.models import CustomUser

        logger.info(f"New email category created: {instance.name}")
