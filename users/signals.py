import logging

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import Signal, receiver
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from utils import referencenumber

from . import models

logger = logging.getLogger(__name__)

#
# Signal for other modules to activate user
#
activate_user = Signal()
#
# Signal for other modules to deactivate user
#
deactivate_user = Signal()
#
# Signal for other modules to handle new users
#
create_user = Signal()
#
# Signal for other modules to handle new membership applications
#
create_application = Signal()
# and application approvals
application_approved = Signal()
# and application denials
application_denied = Signal()


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


@receiver(post_save, sender=models.ServiceSubscription)
def service_subscription_create(
    sender, instance: models.ServiceSubscription, created, raw, **kwargs
):
    if raw:
        return

    if created:
        if instance.reference_number is None:
            refnum = referencenumber.generate(
                settings.SERVICE_INVOICE_REFERENCE_BASE + instance.id
            )
            instance.reference_number = refnum
            instance.save()
            logger.info(
                f"ServiceSubscription {instance} created for user {instance.user} without reference number. Generated reference number {refnum} for it"
            )


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


@receiver(post_save, sender=models.CustomInvoice)
def custominvoice_create(
    sender, instance: models.CustomInvoice, created, raw, **kwargs
):
    """
    When custominvoice is created, generate reference number automatically if it is not defined
    """
    if raw:
        return

    if created:
        if instance.reference_number is None:
            refnum = referencenumber.generate(
                settings.CUSTOM_INVOICE_REFERENCE_BASE + instance.id
            )
            instance.reference_number = refnum
            instance.save()
            logger.info(
                f"CustomInvoice {instance} created for user {instance.user} without reference number. Generated reference number {refnum} for it"
            )


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
    translation.activate(instance.user.language)
    # TODO: maybe move this subject to settings?
    subject = _("Thank you for applying membership and next steps")
    from_email = settings.NOREPLY_FROM_ADDRESS
    to = instance.user.email
    plaintext_content = render_to_string("mail/application_received.txt", context)

    send_mail(subject, plaintext_content, from_email, [to])


@receiver(create_application, sender=models.MembershipApplication)
def send_new_application_waiting_processing_email(
    sender, instance: models.MembershipApplication, **kwargs
):
    """
    send email to admin user so that they notice that there is a new membership application
    """
    logger.info(
        "Sending new application received notification email {}".format(instance)
    )
    context = {
        "user": instance.user,
        "settings": settings,
    }
    subject = _("New membership application received")
    from_email = settings.NOREPLY_FROM_ADDRESS
    to = settings.MEMBERSHIP_APPLICATION_NOTIFY_ADDRESS
    plaintext_content = render_to_string("mail/new_application.txt", context)

    send_mail(subject, plaintext_content, from_email, [to])


@receiver(application_approved, sender=models.MembershipApplication)
def send_application_approved_email(
    sender, instance: models.MembershipApplication, **kwargs
):
    logger.info(
        "Application approved, sending welcome email {}, language {}".format(
            instance, instance.user.language
        )
    )
    context = {
        "user": instance.user,
        "settings": settings,
    }
    translation.activate(instance.user.language)
    # TODO: maybe move this subject to settings?
    subject = _("Your application has been approved")
    from_email = settings.NOREPLY_FROM_ADDRESS
    to = [instance.user.email, settings.MEMBERSHIP_APPLICATION_NOTIFY_ADDRESS]
    plaintext_content = render_to_string("mail/welcome_and_next_steps.txt", context)

    send_mail(subject, plaintext_content, from_email, to)


@receiver(application_denied, sender=models.MembershipApplication)
def send_application_denied_email(
    sender, instance: models.MembershipApplication, **kwargs
):
    logger.info("Application denied, sending bye bye email {}".format(instance))
    context = {
        "user": instance.user,
        "settings": settings,
    }
    translation.activate(instance.user.language)
    # TODO: maybe move this subject to settings?
    subject = _("Your application has been rejected")
    from_email = settings.NOREPLY_FROM_ADDRESS
    to = [instance.user.email, settings.MEMBERSHIP_APPLICATION_NOTIFY_ADDRESS]
    plaintext_content = render_to_string("mail/application_rejected.txt", context)

    send_mail(subject, plaintext_content, from_email, to)


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


#
# Signal door access denied
#
# This allows other modules to catch door opening failures.
# instance is the user object (this signal will only trigger if the user was
# succesfully identified)
# method is the method that was tried (phone, nfc etc)
door_access_denied = Signal()


@receiver(door_access_denied)
def notify_user_door_access_denied(sender, user: models.CustomUser, method, **kwargs):
    context = {
        "user": user,
        "settings": settings,
        "method": method,
    }
    translation.activate(user.language)
    subject = _("Door access denied")
    from_email = settings.NOREPLY_FROM_ADDRESS
    to = [user.email]
    plaintext_content = render_to_string("mail/door_access_denied.txt", context)
    send_mail(subject, plaintext_content, from_email, to, fail_silently=True)
