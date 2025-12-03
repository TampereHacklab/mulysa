from django.utils import timezone
from storage.models import StorageReservation


def complete_finished_reservations():
    """Complete all finished reservations."""
    today = timezone.now().date()
    reservations = StorageReservation.objects.filter(
        status=StorageReservation.ACTIVE, end_date__lt=today
    )
    for res in reservations:
        res.complete()
