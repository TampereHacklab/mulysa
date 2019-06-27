import logging

from django.dispatch import receiver

from users.models import CustomUser
from users.signals import activate_user, deactivate_user

logger = logging.getLogger(__name__)

@receiver(activate_user, sender=CustomUser)
def activate_door_access(sender, instance: CustomUser, **kwargs):
    """
    Send sms to door to activate access for this user
    """
    logger.info('Sending door activation message for user {}'.format(instance))
    # TODO write sms sending to door (twilio or infobip)


@receiver(deactivate_user, sender=CustomUser)
def deactivate_door_access(sender, instance: CustomUser, **kwargs):
    """
    Send sms to door to activate access for this user
    """
    logger.info('Sending door deactivation message for user {}'.format(instance))
    # TODO write sms sending to door (twilio or infobip)
