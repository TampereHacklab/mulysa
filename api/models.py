import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from users.models import NFCCard

logger = logging.getLogger(__name__)


class AccessPermission(models.Model):
    """
    Represents a permission required to use an access target (device).
    For example: 'Cutter permission', or generic access levels.
    """
    name = models.CharField(max_length=255, verbose_name=_("Permission name"))
    code = models.SlugField(max_length=100, unique=True, help_text=_("Short code for the permission"))
    education_required = models.BooleanField(default=False, help_text=_("True if a training/education is required to use targets requiring this permission"))
    description = models.TextField(blank=True, default="", help_text=_("Optional description for this permission"))

    def __str__(self):
        return str(self.name)


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

    DEVICE_TYPE_DOOR = "door"
    DEVICE_TYPE_MACHINE = "machine"
    DEVICE_TYPE_OTHER = "other"

    DEVICE_TYPE_CHOICES = [
        (DEVICE_TYPE_DOOR, "Door"),
        (DEVICE_TYPE_MACHINE, "Machine"),
        (DEVICE_TYPE_OTHER, "Other"),
    ]

    device_type = models.CharField(
        max_length=32,
        choices=DEVICE_TYPE_CHOICES,
        default=DEVICE_TYPE_DOOR,
        help_text=_("What kind of target this device represents (door, machine, ...)")
    )

    # Services that grant access when using this device. If empty, falls back to
    # the previous single-default-service behaviour.
    allowed_services = models.ManyToManyField(
        "users.MemberService",
        blank=True,
        help_text=_("Services that grant access via this device (leave empty for default)"),
    )
    # Permissions that grant access when using this device. If empty, falls back to
    # the previous single-default-service behaviour.
    allowed_permissions = models.ManyToManyField(
        "AccessPermission",
        blank=True,
        help_text=_("Permissions that grant access via this device (leave empty for default)"),
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

    method = models.CharField(
        blank=False,
        verbose_name=_("Method"),
        help_text=_("Method of device access"),
        default="",
        max_length=64,
    )
