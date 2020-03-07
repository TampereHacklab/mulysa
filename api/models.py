import logging

from django.db import models
from django.utils.translation import ugettext_lazy as _

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
        max_length=512,
    )

    # TODO:
    # * which services this device gives access to
    # * extra settings for this device (like how long the access lasts)
    # *
