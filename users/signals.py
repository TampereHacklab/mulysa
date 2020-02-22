import logging

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _

from utils import referencenumber

from . import models

logger = logging.getLogger(__name__)

#
# Signal for other modules to activate user
#
activate_user = Signal(providing_args=["instance", "args", "kwargs"])
#
# Signal for other modules to deactivate user
#
deactivate_user = Signal(providing_args=["instance", "args", "kwargs"])
#
# Signal for other modules to handle new users
#
create_user = Signal(providing_args=["instance", "args", "kwargs"])
#
# Signal for other modules to handle new membership applications
#
create_application = Signal(providing_args=["instance", "args", "kwargs"])
# and application approvals
application_approved = Signal(providing_args=["instance", "args", "kwargs"])
# and application denials
application_denied = Signal(providing_args=["instance", "args", "kwargs"])


@receiver(post_save, sender=models.CustomUser)
def user_creation(sender, instance: models.CustomUser, created, raw, **kwargs):
    """
    After user creation generate required extra information like reference number from the user id

    This is for the models internal use, others should listen to create_user signal which is triggered after
    all the internal things have been done
    """
    if raw:
        return

    if created:
        logger.info("User created: {}".format(instance))
        create_user.send(instance.__class__, instance=instance)
        logger.info("User creation done: {}".format(instance))


@receiver(create_user)
def send_reset_password_email(sender, instance: models.CustomUser, **kwargs):
    """
    When user is created send the reset password email
    """
    form = PasswordResetForm({"email": instance.email})
    from_email = getattr(settings, "NOREPLY_FROM_ADDRESS", "noreply@tampere.hacklab.fi")
    template = "registration/password_reset_email.html"
    form.is_valid()
    form.save(from_email=from_email, email_template_name=template)


@receiver(create_user)
def add_reference_number(sender, instance: models.CustomUser, **kwargs):
    """
    Catch create_user and if the user does not have reference number then add it
    """
    if instance.reference_number is None:
        instance.reference_number = referencenumber.generate(instance.id * 100)
        logger.info(
            "User: {} got newly generated reference number {}".format(
                instance.id, instance.reference_number
            )
        )
        instance.save()
    else:
        logger.info(
            "User: {} already has reference number {}".format(
                instance.id, instance.reference_number
            )
        )


@receiver(post_save, sender=models.MembershipApplication)
def application_creation(
    sender, instance: models.MembershipApplication, created, raw, **kwargs
):
    """
    This is for the models internal use, others should listen to create_application signal which is triggered after
    all the internal things have been done
    """
    if raw:
        return

    if created:
        # now we have the users id and we can generate reference number from it
        # saving it will trigger a new post_save but created will be False (at least I hope so :)
        # as instance id:s start from 1 the reference numbers will be first multiplied by 100
        instance.reference_number = referencenumber.generate(instance.id * 100)
        instance.save()

        logger.info("Membership application created {}".format(instance))
        create_application.send(instance.__class__, instance=instance)
        logger.info("Membership application creation done {}".format(instance))


@receiver(create_application, sender=models.MembershipApplication)
def send_application_received_email(
    sender, instance: models.MembershipApplication, **kwargs
):
    """
    Send email to the user with information about how to proceed next

    Mainly contains information about where to pay and how much and what
    happens next.
    """
    logger.info("Sending thanks for applying membership email to {}".format(instance))
    context = {
        "user": instance.user,
        "settings": settings,
    }
    # TODO: maybe move this subject to settings?
    subject = _("Thank you for applying membership and next steps")
    from_email = settings.NOREPLY_FROM_ADDRESS
    to = instance.user.email
    html_content = render_to_string("mail/application_received.html", context)
    plaintext_content = strip_tags(html_content)

    send_mail(subject, plaintext_content, from_email, [to], html_message=html_content)


@receiver(application_approved, sender=models.MembershipApplication)
def send_application_approved_email(
    sender, instance: models.MembershipApplication, **kwargs
):
    logger.info("Application approved, sending welcome email {}".format(instance))
    context = {
        "user": instance.user,
        "settings": settings,
    }
    # TODO: maybe move this subject to settings?
    subject = _("Your application has been approved")
    from_email = settings.NOREPLY_FROM_ADDRESS
    to = instance.user.email
    html_content = render_to_string("mail/welcome_and_next_steps.html", context)
    plaintext_content = strip_tags(html_content)

    send_mail(subject, plaintext_content, from_email, [to], html_message=html_content)


@receiver(application_denied, sender=models.MembershipApplication)
def send_application_denied_email(
    sender, instance: models.MembershipApplication, **kwargs
):
    logger.info("Application denied, sending bye bye email {}".format(instance))
    context = {
        "user": instance.user,
        "settings": settings,
    }
    # TODO: maybe move this subject to settings?
    subject = _("Your application has been rejected")
    from_email = settings.NOREPLY_FROM_ADDRESS
    to = instance.user.email
    html_content = render_to_string("mail/application_rejected.html", context)
    plaintext_content = strip_tags(html_content)

    send_mail(subject, plaintext_content, from_email, [to], html_message=html_content)


@receiver(pre_save, sender=models.CustomUser)
def send_user_activated(sender, instance: models.CustomUser, raw, **kwargs):
    """
    Before saving the user information check if our is_active changed
    If it did send our activate_user or deactivate_user signals for others
    to handle
    """
    if raw:
        return

    # if is active didn't change don't do anything
    try:
        previous = models.CustomUser.objects.get(id=instance.id)
    except models.CustomUser.DoesNotExist:
        # new user, it wont be activated or deactived yet
        return

    if previous.is_active == instance.is_active:
        return

    if instance.is_active:
        logger.info("User becoming active {}".format(instance))
        activate_user.send(instance.__class__, instance=instance)
        logger.info("User activation done {}".format(instance))

    else:
        logger.info("User becoming deactive {}".format(instance))
        deactivate_user.send(instance.__class__, instance=instance)
        logger.info("User deactivation done {}".format(instance))
