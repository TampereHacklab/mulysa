from rest_framework import serializers

from users.models.bank_transaction import BankTransaction
from users.models.custom_user import CustomUser


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CustomUser
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
        model = CustomUser
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
        model = BankTransaction
        fields = ("aggregatedate", "withdrawals", "deposits")
