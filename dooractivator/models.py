from django.db import models
from django.utils.translation import ugettext_lazy as _


class SMSLog(models.Model):
    """
    Simple sms log, just to keep information on which messages have been sent
    All other information is added as soon as we want to send something but the sid is only
    updated after the operator has accepted the message
    """

    created = models.DateTimeField(
        auto_now_add=True, verbose_name="Creation", help_text="Automatically now"
    )
    from_number = models.CharField(
        null=True, blank=True, verbose_name=_("From number"), max_length=255,
    )
    to_number = models.CharField(
        null=True, blank=True, verbose_name=_("To number"), max_length=255,
    )
    message = models.CharField(
        null=True, blank=True, verbose_name=_("Message"), max_length=255,
    )
    via = models.CharField(
        null=True,
        blank=True,
        verbose_name=_("Via, which operator delivered the message"),
        max_length=255,
    )
    sid = models.CharField(
        null=True,
        blank=True,
        verbose_name=_("Operators ID for the message"),
        help_text=_("this is only added after the operator has accepted the message"),
        max_length=255,
    )
