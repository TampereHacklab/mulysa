from django.db import models
from django.utils.translation import gettext_lazy as _


class StorageService(models.Model):
    """
    Represents a storage service — a logical collection of storage units
    and the related configuration for pricing, rules, and visibility.
    Used as the top-level container for storage locations available for reservation.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Storage service name"),
        help_text=_(
            "A short name for this storage service (e.g. 'Hacklab shelf storage')."
        ),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_("Optional longer description of the storage service."),
    )

    pending_payment_days = models.PositiveIntegerField(
        verbose_name=_("Pending payment period (days)"),
        help_text=_(
            "Number of days a reservation stays pending before expiring if unpaid."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
        help_text=_("Automatically set when this storage service is created"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified"),
        help_text=_("Timestamp when this storage service was last modified"),
    )

    def __str__(self):
        return self.name
