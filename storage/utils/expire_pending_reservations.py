from django.utils import timezone
from storage.models import StorageReservation


def expire_pending_reservations():
    """Expire all unpaid reservations after pending_until date has been passed."""
    today = timezone.now().date()
    for res in StorageReservation.objects.filter(
        status=StorageReservation.PENDING, pending_until__lt=today
    ):
        res.expire_if_unpaid()
