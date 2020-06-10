from datetime import datetime

from django.urls import reverse

from api.models import AccessDevice
from drfx import settings
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import CustomUser, MemberService, ServiceSubscription, NFCCard
from rest_framework.authtoken.models import Token

class TestAccess(APITestCase):
    fixtures = ["users/fixtures/memberservices.json"]

    def setUp(self):
        # create test superuser for authenticated calls
        self.superuser = CustomUser.objects.create_superuser(
            "admin@example.com", "FirstName", "LastName", "+358123", "hunter2"
        )
        self.superuser_token = Token.objects.create(user=self.superuser)

        # create test device
        self.device = AccessDevice.objects.create(deviceid="testdevice",)

        # and test user
        self.ok_user = CustomUser.objects.create(
            email="test1@example.com", birthday=datetime.now(), phone="+35844055066"
        )
        self.ok_user.save()

        # add subscription for the user
        self.ok_subscription = ServiceSubscription.objects.create(
            user=self.ok_user,
            service=MemberService.objects.get(pk=settings.DEFAULT_ACCOUNT_SERVICE),
            state=ServiceSubscription.ACTIVE,
        )
        self.ok_subscription.save()

        # and test card
        self.ok_card = NFCCard.objects.create(user=self.ok_user, cardid="ABC123TEST",)
        self.ok_card.save()
        # and another test card for the same user
        self.ok_card2 = NFCCard.objects.create(user=self.ok_user, cardid="ABC123TEST2",)
        self.ok_card2.save()

        # user with no access
        self.fail_user = CustomUser.objects.create(
            email="test2@example.com", birthday=datetime.now(), phone="+35855044033"
        )
        # with suspended service
        self.fail_subscription = ServiceSubscription.objects.create(
            user=self.fail_user,
            service=MemberService.objects.get(pk=settings.DEFAULT_ACCOUNT_SERVICE),
            state=ServiceSubscription.SUSPENDED,
        )
        # and a test card for fail case
        self.not_ok_card = NFCCard.objects.create(
            user=self.fail_user, cardid="TESTABC",
        )
        self.not_ok_card.save()

        self.fail_subscription.save()

    def test_access_phone_no_payload(self):
        """
        Test with missing payload
        """
        url = reverse("access-phone")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": ""}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_access_phone_not_found(self):
        """
        Test with not found number
        """
        url = reverse("access-phone")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": "+358111111111"}
        )
        self.assertEqual(response.status_code, 480)

    def test_access_phone_list_unauthenticated(self):
        url = reverse("access-phone")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_phone_list_wrongauth(self):
        url = reverse("access-phone")
        response = self.client.get(
            url, HTTP_AUTHORIZATION="Token {}".format("invalidtoken")
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_phone_list_authenticated(self):
        url = reverse("access-phone")
        response = self.client.get(
            url, HTTP_AUTHORIZATION="Token {}".format(self.superuser_token)
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.ok_user.phone)
        self.assertContains(response, self.ok_user.email)
        self.assertNotContains(response, self.fail_user.phone)
        self.assertNotContains(response, self.fail_user.email)

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
        self.assertEqual(response.status_code, 481)

    def test_access_phone_empty(self):
        url = reverse("access-phone")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": ""}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_device(self):
        url = reverse("access-phone")
        response = self.client.post(
            url, {"deviceid": "not_a_valid_device", "payload": self.ok_user.phone}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nfc_ok(self):
        url = reverse("access-nfc")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": self.ok_card.cardid}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nfc_ok2(self):
        url = reverse("access-nfc")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": self.ok_card2.cardid}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_nfc_notok(self):
        url = reverse("access-nfc")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": self.not_ok_card.cardid}
        )
        self.assertEqual(response.status_code, 481)

    def test_nfc_empty(self):
        url = reverse("access-nfc")
        response = self.client.post(
            url, {"deviceid": self.device.deviceid, "payload": ""}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def tearDown(self):
        CustomUser.objects.all().delete()
        Token.objects.all().delete()
