import logging

from django.conf import settings
from django.dispatch import receiver

from users.models import CustomUser
from users.signals import activate_user, deactivate_user

from .sms_twilio import SMSTwilio

logger = logging.getLogger(__name__)


@receiver(activate_user, sender=CustomUser)
def activate_door_access(sender, instance: CustomUser, **kwargs):
    """
    Send sms to door to activate access for this user
    """
    logger.info("Sending door activation message for user {}".format(instance))

    if not settings.SMS.get("ENABLED"):
        logger.info("SMS sending disabled in settings")
        return

    if not instance.phone:
        logger.info("No phone number defined, not trying to activate")
        return

    try:
        twilio = SMSTwilio()
        twilio.initialize(
            sid=settings.SMS.get("TWILIO_SID"),
            token=settings.SMS.get("TWILIO_TOKEN"),
            from_number=settings.SMS.get("TWILIO_FROM"),
        )
        msg = twilio.build_activate_access_message(
            number=instance.phone, name=instance.get_short_name()
        )
        twilio.send_sms(to_number=settings.SMS.get("TO_NUMBER"), message=msg)
    except Exception:
        logger.exception("SMS sending failed")


@receiver(deactivate_user, sender=CustomUser)
def deactivate_door_access(sender, instance: CustomUser, **kwargs):
    """
    Send sms to door to activate access for this user
    """
    logger.info("Sending door deactivation message for user {}".format(instance))

    if not settings.SMS.get("ENABLED"):
        logger.info("SMS sending disabled in settings")
        return

    if not instance.phone:
        logger.info("No phone number defined, not trying to deactivate")
        return

    try:
        twilio = SMSTwilio()
        twilio.initialize(
            sid=settings.SMS.get("TWILIO_SID"),
            token=settings.SMS.get("TWILIO_TOKEN"),
            from_number=settings.SMS.get("TWILIO_FROM"),
        )
        msg = twilio.build_deactivate_access_message(
            number=instance.phone, name=instance.get_short_name()
        )
        twilio.send_sms(to_number=settings.SMS.get("TO_NUMBER"), message=msg)
    except Exception:
        logger.exception("SMS sending failed")
