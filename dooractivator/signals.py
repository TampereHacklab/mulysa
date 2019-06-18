from users.signals import activate_user, deactivate_user
from django.dispatch import receiver
from api.exceptions import NotImplementedYet
from users.models import CustomUser


@receiver(activate_user, sender=CustomUser)
def activate_door_access(sender, instance: CustomUser, **kwargs):
    """
    Send sms to door to activate access for this user
    """
    print("Activating door access for user {}".format(instance))
    # TODO write sms sending to door (twilio or infobip)


@receiver(deactivate_user, sender=CustomUser)
def deactivate_door_access(sender, instance: CustomUser, **kwargs):
    """
    Send sms to door to activate access for this user
    """
    print("DEActivating door access for user {}".format(instance))
    raise NotImplementedYet
    # TODO write sms sending to door (twilio or infobip)
