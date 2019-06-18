from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.dispatch import Signal

from . import models

#
# Signal for other modules to activate user
#
activate_user = Signal(providing_args=["instance", "args", "kwargs"])
#
# Signal for other modules to deactivate user
#
deactivate_user = Signal(providing_args=["instance", "args", "kwargs"])

@receiver(pre_save, sender=models.CustomUser)
def send_user_activated(sender, instance: models.CustomUser, raw, **kwargs):
    """
    Before saving the user information check if our is_active changed
    If it did send our activate_user or deactivate_user signals for others
    to handle
    """
    if raw:
        # probably loading fixtures, don't do it
        return

    # if is active didn't change don't do anything
    previous = models.CustomUser.objects.get(id=instance.id)
    if previous.is_active == instance.is_active:
        return

    if instance.is_active:
        print("User getting activated")
        activate_user.send(instance.__class__, instance=instance)

    else:
        print("User getting deactivated")
        deactivate_user.send(instance.__class__, instance=instance)
