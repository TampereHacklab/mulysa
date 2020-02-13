from rest_framework import serializers
from users.models import CustomUser


class AccessDataSerializer(serializers.Serializer):
    """
    Serializer for incoming access data
    """
    deviceid = serializers.CharField(max_length=200)
    payload = serializers.CharField(max_length=200)


class UserAccessSerializer(serializers.HyperlinkedModelSerializer):
    """
    Serializer for user access data return
    """
    class Meta:
        model = CustomUser
        fields = (
            "email",
            "first_name",
            "last_name",
            "phone",
        )
        read_only_fields = ("is_active",)
