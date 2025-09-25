from rest_framework import serializers
from .. import models
from django.utils import timezone
from dateutil.relativedelta import relativedelta


class StorageSerializer(serializers.ModelSerializer):
    """Basic information about storage service"""

    class Meta:
        model = models.StorageService
        fields = ("name", "description", "pending_payment_days", "created_at")


class StorageUnitSerializer(serializers.ModelSerializer):
    """Show storage unit information"""

    service = StorageSerializer()

    class Meta:
        model = models.StorageUnit
        fields = (
            "service",
            "name",
            "is_disabled",
            "price_per_month",
            "max_rental_months",
            "description",
            "show_name_publicly",
            "allow_self_subscription",
            "created_at",
        )


class StorageReservationSerializer(serializers.ModelSerializer):
    """Show reservation information (read only)"""

    unit = StorageUnitSerializer(read_only=True)

    class Meta:
        model = models.StorageReservation
        fields = (
            "unit",
            "start_date",
            "end_date",
            "status",
            "total_paid_months",
            "max_duration_months",
            "reference_number",
            "pending_until",
            "paid_at",
            "created_at",
        )
        read_only_fields = (
            "status",
            "reference_number",
            "pending_until",
            "paid_at",
            "created_at",
        )


class StorageReservationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new reservation

      Performs business rule validations:
    - Unit cannot already be reserved for the given period
    - Reservation cannot exceed max_rental_months
    - Storage unit must be active (not disabled)
    - Storage service must allow self-subscription (if required)
    - User can only have one active/pending reservation at a time
    """

    duration_months = serializers.IntegerField(
        min_value=1, required=True, write_only=True
    )

    class Meta:
        model = models.StorageReservation
        fields = ("unit", "duration_months")

    def validate(self, data):
        user = self.context["request"].user
        unit = data.get("unit")
        duration_months = data.get("duration_months")

        if not unit:
            raise serializers.ValidationError("Storage unit is required.")

        if duration_months < 1:
            raise serializers.ValidationError("Duration must be at least 1 month.")

        if unit.is_disabled:
            raise serializers.ValidationError(
                "This storage unit is currently disabled."
            )

        if not unit.allow_self_subscription:
            raise serializers.ValidationError(
                "Self-subscription is not allowed for this storage unit."
            )

        if unit.max_rental_months and duration_months > unit.max_rental_months:
            raise serializers.ValidationError(
                f"Reservation cannot exceed {unit.max_rental_months} months."
            )

        start_date = timezone.now().date()
        end_date = start_date + relativedelta(months=duration_months)

        overlapping = models.StorageReservation.objects.filter(
            unit=unit,
            status__in=[
                models.StorageReservation.ACTIVE,
                models.StorageReservation.PENDING,
            ],
        ).filter(
            start_date__lt=end_date,
            end_date__gt=start_date,
        )

        if overlapping.exists():
            raise serializers.ValidationError(
                f"Storage unit {unit.name} is already reserved or pending."
            )

        if not user.is_staff and not user.is_superuser:
            existing_reservation = models.StorageReservation.objects.filter(
                user=user,
                status__in=[
                    models.StorageReservation.ACTIVE,
                    models.StorageReservation.PENDING,
                ],
            )
            if existing_reservation.exists():
                raise serializers.ValidationError(
                    "You already have an active or pending reservation."
                )

        data["start_date"] = start_date
        data["end_date"] = end_date
        return data

    def create(self, validated_data):
        """Create reservation object that starts today and lasts given months."""
        validated_data.pop("duration_months")
        return models.StorageReservation.objects.create(**validated_data)
