from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from storage.models import StorageUnit
from storage.serializers.admin_serializers import (
    StorageUnitAdminSerializer,
    StorageReservationHistorySerializer,
)


class StorageAdminViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin viewset to list storage units and their reservations.
    """

    queryset = StorageUnit.objects.all()
    serializer_class = StorageUnitAdminSerializer

    @action(detail=True, methods=["get"])
    def reservation_history(self, request, pk=None):
        """
        Return all reservations for a given unit.
        """
        unit = self.get_object()
        reservations = unit.storagereservation_set.all()
        serializer = StorageReservationHistorySerializer(reservations, many=True)
        return Response(serializer.data)
