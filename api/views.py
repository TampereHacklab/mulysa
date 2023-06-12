import logging

from django.shortcuts import get_object_or_404

from api.serializers import AccessDataSerializer, UserAccessSerializer
from drfx import config as config
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_tracking.mixins import LoggingMixin
from users.models import CustomUser, NFCCard, ServiceSubscription

from utils.phonenumber import normalize_number

from .models import AccessDevice, DeviceAccessLogEntry
from users.signals import door_access_denied

logger = logging.getLogger(__name__)


class VerySlowThrottle(AnonRateThrottle):
    """
    Throttle for access views
    """

    rate = "10/minute"


class AccessViewSet(LoggingMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    Access checker api

    contains few sub endpoints like phone, mxid and nfc that can be used to check one user
    with one access method.

    When for example phone endpoint is called with a post it will try to check the incoming
    deviceid and payload against the database and return 200 ok if the user has access.

    Get request to the same phone endpoint will return a list of all active users.

    Also throws erros for all default actions TODO: there is probably a cleaner way to do this
    """

    throttle_classes = [VerySlowThrottle]
    permission_classes = []
    # default to AccessDataSerializer for all methods
    serializer_class = AccessDataSerializer
    # default queryset as none
    queryset = CustomUser.objects.none

    @action(detail=False, methods=["post"], throttle_classes=[VerySlowThrottle])
    def phone(self, request, format=None):
        """
        Check if the phone number is allowed to access and return some user data
        to caller.

        call with something like this
        http POST http://127.0.0.1:8000/api/v1/access/phone/ deviceid=asdf payload=0440431918

        returns 200 ok with some user data if everything is fine and 4XX for other situations

        users with enough power will also get a list of all users with door access with this endpoint
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

        # our user
        user = qs.first()

        # user does not have access rights
        if not user.has_door_access():
            user.log("Door access denied with phone")
            door_access_denied.send(sender=self.__class__, user=user, method="phone")
            outserializer = UserAccessSerializer(user)
            return Response(outserializer.data, status=481)

        user.log("Door opened with phone")
        outserializer = UserAccessSerializer(user)
        return Response(outserializer.data)

    @phone.mapping.get
    def phone_list(self, request, format=None):
        """
        List all phone access users
        """
        # only for superusers
        if not request.user or not request.user.is_superuser:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        # collect list of all users that have door access
        users_with_door_access = []
        for ss in (
            ServiceSubscription.objects.select_related("user")
            .filter(service=config.DEFAULT_ACCOUNT_SERVICE)
            .filter(state=ServiceSubscription.ACTIVE)
        ):
            users_with_door_access.append(ss.user)

        # and output it
        outserializer = UserAccessSerializer(users_with_door_access, many=True)
        return Response(outserializer.data)

    @action(detail=False, methods=["post"], throttle_classes=[VerySlowThrottle])
    def nfc(self, request, format=None):
        """
        NFC card access
        """
        logentry = DeviceAccessLogEntry()
        inserializer = AccessDataSerializer(data=request.data)
        inserializer.is_valid(raise_exception=True)

        deviceqs = AccessDevice.objects.all()
        deviceid = inserializer.validated_data.get("deviceid")
        device = get_object_or_404(deviceqs, deviceid=deviceid)
        logging.debug(f"found device {device}")

        cardid = inserializer.validated_data.get("payload")
        qs = NFCCard.objects.filter(cardid=cardid)

        logentry.device = device
        logentry.payload = cardid

        # 0 = success, any other = failure
        response_status = 0

        if qs.count() == 0:
            response_status = 480
        else:
            logentry.nfccard = qs.first()

            # our user
            user = qs.first().user

            # user does not have access rights
            if not user.has_door_access():
                user.log("Door access denied with NFC")
                door_access_denied.send(sender=self.__class__, user=user, method="nfc")
                response_status = 481

        logentry.granted = response_status == 0

        logentry.save()

        if response_status == 0:
            user.log("Door opened with NFC")
            outserializer = UserAccessSerializer(user)
            return Response(outserializer.data)

        if response_status == 481:
            outserializer = UserAccessSerializer(user)
            return Response(outserializer.data, status=response_status)

        return Response(status=response_status)

    @action(detail=False, methods=["post"], throttle_classes=[VerySlowThrottle])
    def mxid(self, request, format=None):
        """
        Matrix mxid access
        """
        logentry = DeviceAccessLogEntry()
        inserializer = AccessDataSerializer(data=request.data)
        inserializer.is_valid(raise_exception=True)

        deviceqs = AccessDevice.objects.all()
        deviceid = inserializer.validated_data.get("deviceid")
        device = get_object_or_404(deviceqs, deviceid=deviceid)
        logging.debug(f"found device {device}")

        mxid = inserializer.validated_data.get("payload")
        users = CustomUser.objects.filter(mxid=mxid)

        logentry.device = device
        logentry.payload = mxid

        # 0 = success, any other = failure
        response_status = 0

        if users.count() != 1:
            response_status = 480
        else:
            user = users.first()

            # user does not have access rights
            if not user.has_door_access():
                door_access_denied.send(sender=self.__class__, user=user, method="mxid")
                response_status = 481

        logentry.granted = response_status == 0
        logentry.save()

        if response_status == 0:
            outserializer = UserAccessSerializer(user)
            return Response(outserializer.data)

        if response_status == 481:
            outserializer = UserAccessSerializer(user)
            return Response(outserializer.data, status=response_status)

        return Response(status=response_status)

    def list(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
