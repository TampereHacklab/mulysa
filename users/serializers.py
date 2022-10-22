from rest_framework import serializers

from . import models


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.CustomUser
        fields = (
            "url",
            "email",
            "first_name",
            "last_name",
            "phone",
            "is_active",
            "is_staff",
            "created",
            "last_modified",
            "marked_for_deletion_on",
            "birthday",
            "nick",
            "municipality",
        )
        read_only_fields = (
            "is_active",
            "is_staff",
            "created",
            "last_modified",
            "marked_for_deletion_on",
        )


class UserActivationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.CustomUser
        fields = ("is_active",)
        extra_kwargs = {"is_active": {"required": True}}


class BankTransactionAggregateSerializer(serializers.Serializer):
    """
    Serializer for BankTransactionAggregate data
    """

    aggregatedate = serializers.DateField()
    withdrawals = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )
    deposits = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=False
    )

    class Meta:
        model = models.BankTransaction
        fields = ("aggregatedate", "withdrawals", "deposits")
