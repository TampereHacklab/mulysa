from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import StorageService, StorageUnit, StorageReservation
from ..serializers.reservation_serializers import (
    StorageSerializer,
    StorageUnitSerializer,
    StorageReservationSerializer,
    StorageReservationCreateSerializer,
)
from django.utils import timezone
from datetime import timedelta
from utils import referencenumber
from users.signals import reservation_created


class StorageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Show all storages (read only)
    """

    queryset = StorageService.objects.all()
    serializer_class = StorageSerializer


class StorageUnitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Show all storage units (read only)
    """

    queryset = StorageUnit.objects.all()
    serializer_class = StorageUnitSerializer


class ReservationViewSet(viewsets.ModelViewSet):
    """
    Creates a new reservation for a storage unit.
    Sets automatically:
      - status = PENDING
      - reference_number = reference number
      - pending_until = the date the reservation has to be paid
    """
    permission_classes = [IsAuthenticated]
    queryset = StorageReservation.objects.select_related("unit").all()

    def get_serializer_class(self):
        if self.action == "create":
            return StorageReservationCreateSerializer
        return StorageReservationSerializer

    def perform_create(self, serializer):
        ref_number = str(referencenumber.generate_random(1000000, 9999999))

        reservation = serializer.save(
            user=self.request.user,
            status=StorageReservation.PENDING,
            reference_number=ref_number,
        )

        service = reservation.unit.service
        reservation.pending_until = timezone.now().date() + timedelta(
            days=service.pending_payment_days
        )

        reservation.max_duration_months = reservation.unit.max_rental_months
        reservation.save()

        # Send confirmation email
        reservation_created.send(
            sender=self.__class__,
            instance=reservation,
        )
