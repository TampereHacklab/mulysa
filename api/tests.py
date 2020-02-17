from datetime import datetime

from django.urls import reverse

from api.models import AccessDevice
from drfx import settings
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import CustomUser, MemberService, ServiceSubscription


class TestAccess(APITestCase):
    fixtures = ["users/fixtures/memberservices.json"]

    def setUp(self):
        self.device = AccessDevice.objects.create(
            deviceid="testdevice",
        )
        self.ok_user = CustomUser.objects.create(
            email="test1@example.com", birthday=datetime.now(), phone="+35844055066"
        )
        self.ok_user.save()
        self.ok_subscription = ServiceSubscription.objects.create(
            user=self.ok_user,
            service=MemberService.objects.get(pk=settings.DEFAULT_ACCOUNT_SERVICE),
            state=ServiceSubscription.ACTIVE,
        )
        self.ok_subscription.save()
        self.fail_user = CustomUser.objects.create(
            email="test2@example.com", birthday=datetime.now(), phone="+35855044033"
        )
        self.fail_subscription = ServiceSubscription.objects.create(
            user=self.fail_user,
            service=MemberService.objects.get(pk=settings.DEFAULT_ACCOUNT_SERVICE),
            state=ServiceSubscription.SUSPENDED,
        )
        self.fail_subscription.save()

    def test_access_phone_no_payload(self):
        """
        Test with missing payload
        """
        url = reverse("access-phone")
        response = self.client.post(url, {"deviceid": self.device.deviceid, "payload": ""})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_access_phone_ok(self):
        """
        Test with ok user and phone number
        """
        url = reverse("access-phone")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": self.ok_user.phone}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_phone_notok(self):
        url = reverse("access-phone")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": self.fail_user.phone}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_device(self):
        url = reverse("access-phone")
        response = self.client.post(
            url, {"deviceid": "not_a_valid_device", "payload": self.ok_user.phone}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def tearDown(self):
        for user in CustomUser.objects.all():
            user.delete()
