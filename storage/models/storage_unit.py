from django.db import models
from django.utils.translation import gettext_lazy as _
from storage.models.storage_service import StorageService
from django.apps import apps


class StorageUnit(models.Model):
    """
    Represents an individual storage location (e.g. a shelf or a pallet spot)
    within a StorageService. Each unit can have its own pricing, visibility,
    and reservation rules.
    """

    service = models.ForeignKey(StorageService, on_delete=models.CASCADE)

    name = models.CharField(
        max_length=50,
        verbose_name=_("Name"),
        help_text=_("Name or identifier of the unit"),
    )

    is_disabled = models.BooleanField(
        default=False,
        verbose_name=_("Disabled"),
        help_text=_(
            "If true, this unit cannot be reserved (e.g. blocked or permanently occupied)."
        ),
    )

    price_per_month = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        verbose_name=_("Price per month"),
        help_text=_("Monthly price for renting this storage unit"),
    )

    max_rental_months = models.PositiveIntegerField(
        verbose_name=_("Maximum rental duration (months)"),
        help_text=_("Maximum allowed rental duration for this storage unit"),
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Description"),
        help_text=_(
            "Optional description for this storage unit (e.g. dimensions, location details)."
        ),
    )

    allow_self_subscription = models.BooleanField(
        default=True,
        verbose_name=_("Allow self-subscription"),
        help_text=_(
            "If true, users can reserve this unit themselves without admin approval."
        ),
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created at"),
        help_text=_("Automatically set when this storage unit is created"),
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified"),
        help_text=_("Timestamp when this unit was last modified"),
    )

    def __str__(self):
        return f"{self.name}"

    def calculate_price(self, months=1):
        """Calculate the total rental price based on the number of months."""
        return self.price_per_month * months

    def disable(self):
        self.is_disabled = True
        self.save(update_fields=["is_disabled"])

    def enable(self):
        self.is_disabled = False
        self.save(update_fields=["is_disabled"])

    def current_reservation(self):
        """Return the active reservation for this unit, if one exists."""
        StorageReservation = apps.get_model("storage", "StorageReservation")
        return StorageReservation.objects.filter(
            unit=self,
            status__in=[StorageReservation.ACTIVE, StorageReservation.PENDING],
        ).first()

    def get_current_renter_admin(self):
        """Return the renter's name (for admin use)."""
        reservation = self.current_reservation()
        if reservation:
            return reservation.user.get_full_name() or reservation.user.username
        return None

    def current_reference_number(self):
        """Return the active reservation’s payment reference number, if any."""
        reservation = self.current_reservation
        return reservation.reference_number if reservation else None

    def reservation_history(self):
        """Return all reservation related to this unit."""
        return self.storagereservation_set.order_by("-start_date")

    @property
    def status(self):
        """Return the current status of the unit as a human-readable string."""
        StorageReservation = apps.get_model("storage", "StorageReservation")
        if self.is_disabled:
            return _("Disabled")

        active_reservations = StorageReservation.objects.filter(
            unit=self,
            status__in=[StorageReservation.ACTIVE, StorageReservation.PENDING],
        )

        if active_reservations.exists():
            return _("Reserved")
        return _("Available")
