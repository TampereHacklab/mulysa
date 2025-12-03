from rest_framework import serializers
from storage.models import StorageUnit, StorageReservation


class StorageReservationHistorySerializer(serializers.ModelSerializer):
    """Reservation history"""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = StorageReservation
        fields = [
            "user_email",
            "user_name",
            "status",
            "start_date",
            "end_date",
            "total_paid_months",
        ]


class StorageUnitAdminSerializer(serializers.ModelSerializer):
    """Storage unit information and reservations."""

    reservations = StorageReservationHistorySerializer(
        many=True, source="storagereservation_set", read_only=True
    )

    class Meta:
        model = StorageUnit
        fields = [
            "name",
            "service",
            "price_per_month",
            "max_rental_months",
            "reservations",
        ]
