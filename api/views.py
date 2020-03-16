import logging

from django.shortcuts import get_object_or_404

from api.serializers import AccessDataSerializer, UserAccessSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_tracking.mixins import LoggingMixin
from users.models import CustomUser, NFCCard, ServiceSubscription

from utils.phonenumber import normalize_number

from .models import AccessDevice

logger = logging.getLogger(__name__)


class VerySlowThrottle(AnonRateThrottle):
    """
    Throttle for access views
    """

    rate = "10/minute"


class AccessViewSet(LoggingMixin, viewsets.GenericViewSet):
    """
    Access checker api

    Currently only implements phone

    Also throws erros for all default actions TODO: there is probably a cleaner way to do this
    """

    throttle_classes = [VerySlowThrottle]
    permission_classes = []

    def get_serializer_class(self):
        pass

    @action(detail=False, methods=["post"], throttle_classes=[VerySlowThrottle])
    def phone(self, request, format=None):
        """
        Check if the phone number is allowed to access and return some user data
        to caller.

        call with something like this
        http POST http://127.0.0.1:8000/api/v1/access/phone/ deviceid=asdf payload=0440431918

        returns 200 ok with some user data if everything is fine and 4XX for other situations
        """
        inserializer = AccessDataSerializer(data=request.data)
        inserializer.is_valid(raise_exception=True)

        # check that we know which device this is
        deviceqs = AccessDevice.objects.all()
        deviceid = inserializer.validated_data.get("deviceid")
        device = get_object_or_404(deviceqs, deviceid=deviceid)
        logging.debug(f"found device {device}")

        # phone number comes in payload, but it is in a wrong format
        # the number will most probably start with 00 instead of +

        number = inserializer.validated_data.get("payload")
        number = normalize_number(number)
        qs = CustomUser.objects.filter(phone=number)

        # nothing found, 480
        if qs.count() == 0:
            return Response(status=480)

        # multiple users found. this cannot work...
        if qs.count() != 1:
            logger.error(
                f"Found multiple users with number: {number} this should not happen"
            )
            return Response(status=status.HTTP_409_CONFLICT)

        # our user
        user = qs.first()

        # user does not have access rights
        if not user.is_active:
            return Response(status=481)

        if not user.has_door_access():
            return Response(status=481)

        outserializer = UserAccessSerializer(user)
        return Response(outserializer.data)

    @action(detail=False, methods=["post"], throttle_classes=[VerySlowThrottle])
    def nfc(self, request, format=None):
        """
        NFC card access
        """
        inserializer = AccessDataSerializer(data=request.data)
        inserializer.is_valid(raise_exception=True)

        cardid = inserializer.validated_data.get("payload")
        qs = NFCCard.objects.filter(cardid=cardid)

        if qs.count() == 0:
            return Response(status=480)

        # our user
        user = qs.first().user
        # user does not have access rights
        if not user.is_active:
            return Response(status=481)

        if qs.first().subscription.state != ServiceSubscription.ACTIVE:
            return Response(status=481)

        outserializer = UserAccessSerializer(user)
        return Response(outserializer.data)

    def list(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def create(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def retrieve(self, request, pk=None):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def update(self, request, pk=None):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def partial_update(self, request, pk=None):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk=None):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
