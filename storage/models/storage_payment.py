from django.db import models
from django.utils.translation import gettext_lazy as _
from storage.models.storage_reservation import StorageReservation


class StoragePayment(models.Model):
    """
    Represents a payment made toward a storage reservation.
    May be automatically verified via Nordigen.
    """

    reservation = models.ForeignKey(
        StorageReservation,
        on_delete=models.CASCADE,
        verbose_name=_("Related reservation"),
    )

    reference_number = models.CharField(
        blank=True,
        null=True,
        db_index=True,
        max_length=25,
        verbose_name=_("Reference number"),
        help_text=_(
            "Reference number used for this payment (same as reservation reference)"
        ),
    )

    amount = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name=_("Amount (€)"),
        help_text=_("Total amount of money paid for this reservation."),
    )

    months = models.IntegerField(
        verbose_name=_("Paid months"),
        help_text=_("How many months of storage this payment covers."),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
        help_text=_("Automatically set when the payment record is created"),
    )

    paid_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Payment date"),
        help_text=_("Date when payment was received"),
    )

    def __str__(self):
        return f"{self.amount} € for reservation {self.reservation.id} ({self.reference_number})"
