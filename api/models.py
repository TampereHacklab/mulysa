import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from users.models import NFCCard

logger = logging.getLogger(__name__)


class AccessDevice(models.Model):
    """
    Device thingy, used by access service to know what to do
    """

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("User creation date"),
        help_text=_("Automatically set to now when user is create"),
    )

    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified datetime"),
        help_text=_("Last time this user was modified"),
    )

    name = models.CharField(
        verbose_name=_("Device name"),
        help_text=_("Human readable name for the device, like door or laser"),
        max_length=512,
    )
    deviceid = models.CharField(
        unique=True,
        verbose_name=_("device id"),
        help_text=_("used to know which device this was"),
        max_length=255,
    )

    # TODO:
    # * which services this device gives access to
    # * extra settings for this device (like how long the access lasts)
    # *


class DeviceAccessLogEntry(models.Model):
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date of this entry"),
        help_text=_("Automatically set to now when created"),
    )

    granted = models.BooleanField(
        verbose_name=_("Granted"), help_text=_("Was the access granted")
    )

    device = models.ForeignKey(
        AccessDevice,
        null=True,
        verbose_name=_("Device this event came from"),
        on_delete=models.SET_NULL,
    )

    payload = models.CharField(
        blank=False,
        null=True,
        verbose_name=_("NFC card id or phone number, or other field like that"),
        max_length=255,
    )

    nfccard = models.ForeignKey(
        NFCCard,
        null=True,
        verbose_name=_("NFC card"),
        help_text=_("NFC card this was mapped to, if any"),
        on_delete=models.SET_NULL,
    )

    claimed_by = models.ForeignKey(
        get_user_model(),
        null=True,
        verbose_name=_("Claimed by"),
        help_text=_("Who claimed this entry"),
        on_delete=models.SET_NULL,
    )
