from api.models import AccessDevice, DeviceAccessLogEntry
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import MemberService, ServiceSubscription


class TestBasicSmoke(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )

    def test_index_anon(self):
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(response, "Wanna join us")
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="fi")
        self.assertContains(response, "Haluatko liittyä")

    def test_secured_urls(self):
        """
        Just very crude test that the urls don't give 200 ok when not logged in
        """
        urls = [
            reverse("dataimport"),
            reverse("dataexport"),
            reverse("users"),
            reverse("users/create"),
            reverse("ledger"),
            reverse("custominvoices"),
            reverse("userdetails", args=(self.user.id,)),
            reverse("usersettings", args=(self.user.id,)),
            reverse("usersettings_subscribe_service", args=(self.user.id,)),
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            reverse("usersettings_claim_nfc", args=(self.user.id,)),
            reverse("usersettings_delete_nfc", args=(self.user.id,)),
            reverse("custominvoice"),
            reverse("custominvoice_action", args=("test", 1)),
            reverse("application_operation", args=(1, "test")),
            reverse("banktransaction-view", args=(1,)),
        ]
        self.client.logout()
        for url in urls:
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
            self.assertNotEqual(response.status_code, 200)

        # and some urls we should not see as basic logged in user
        self.client.force_login(self.user)
        ownurls = [
            reverse("dataimport"),
            reverse("dataexport"),
            reverse("users"),
            reverse("users/create"),
            reverse("ledger"),
            reverse("custominvoices"),
            reverse("application_operation", args=(1, "test")),
        ]
        for url in ownurls:
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
            self.assertNotEqual(response.status_code, 200)

    def test_index_logged(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(response, "Welcome back")
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="fi")
        self.assertContains(response, "Tervetuloa takaisin")

    def tearDown(self):
        get_user_model().objects.all().delete()


class TestUserViews(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.client.force_login(self.user)
        # test service
        self.memberservice = MemberService.objects.create(
            name="TestService", cost=10, days_per_payment=30, days_before_warning=2
        )

    def test_my_info(self):
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)

        userdetails = response.context["userdetails"]
        self.assertEqual(len(userdetails.servicesubscriptions), 0)
        self.assertEqual(len(userdetails.transactions), 0)
        self.assertEqual(len(userdetails.custominvoices), 0)

    def test_update_data(self):
        # get data
        response = self.client.get(
            reverse("usersettings", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)

        # post new data and check
        response = self.client.post(
            reverse("usersettings", args=(self.user.id,)),
            {"first_name": "New", "last_name": "Test"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New")
        self.assertContains(response, "Test")

    def test_subscribe_unsubscribe_invalid_data(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(9999,)),
            {"serviceid": self.memberservice.id},
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # redirect to login as id does not match
        self.assertRedirects(
            response,
            reverse("login")
            + "?next="
            + reverse("usersettings_subscribe_service", args=(9999,)),
        )

        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(9999,)),
            {"serviceid": self.memberservice.id},
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # redirect to login as id does not match
        self.assertRedirects(
            response,
            reverse("login")
            + "?next="
            + reverse("usersettings_unsubscribe_service", args=(9999,)),
        )

        # become staff
        self.user.is_staff = True
        self.user.save()

        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(9999,)),
            {"serviceid": self.memberservice.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # user not found
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(9999,)),
            {"serviceid": self.memberservice.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # user not found
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(self.user.id,)),
            {"serviceid": 9999},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # service not found
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            {"subscriptionid": 9999},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # service not found
        self.assertEqual(response.status_code, 404)

        self.client.logout()

    def test_subscribe_unsubscribe(self):
        # service not self subscribe
        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(self.user.id,)),
            {"serviceid": self.memberservice.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "This service cannot be self subscribed to")

        # change the service
        self.memberservice.self_subscribe = True
        self.memberservice.save()

        # subscibe again
        response = self.client.post(
            reverse("usersettings_subscribe_service", args=(self.user.id,)),
            {"serviceid": self.memberservice.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]), "Service subscribed. You may now pay for it."
        )

        # and check that we see it
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertEqual(len(response.context["userdetails"].servicesubscriptions), 1)

        # unsubscribe when not paid
        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            {"subscriptionid": self.user.servicesubscription_set.first().id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "Service is not active. You must pay for the service first. Contact staff if needed.",
        )

        # change the service to active
        ss = self.user.servicesubscription_set.first()
        ss.state = ServiceSubscription.ACTIVE
        ss.save()

        # unsubscribe again
        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            {"subscriptionid": ss.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Service unsubscribed")

        # check that our log has the entries
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(
            response,
            f"Self subscribed to {self.memberservice.name}",
        )
        self.assertContains(
            response,
            f"Self unsubscribing from {self.memberservice.name}",
        )

    def tearDown(self):
        get_user_model().objects.all().delete()


class TestStaffViews(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="Test",
            last_name="Admin",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.client.force_login(self.user)

    def smokeViews(self):
        urls = [
            reverse("dataimport"),
            reverse("dataexport"),
            reverse("users"),
            reverse("users/create"),
            reverse("ledger"),
            reverse("custominvoices"),
            reverse("custominvoice"),
            reverse("custominvoice_action", args=("test", 1)),
            reverse("application_operation", args=(1, "test")),
        ]
        for url in urls:
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
            self.assertEqual(response.status_code, 200)

    def tearDown(self):
        get_user_model().objects.all().delete()


class TestNFC(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_customuser(
            first_name="Test",
            last_name="Admin",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.client.force_login(self.user)

    def test_nfc(self):
        # no cards have been seen
        response = self.client.get(
            reverse("usersettings", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(
            response,
            "No recent unclaimed NFC cards. Go to door, use a card and claim it here in 5 minutes",
        )

        # simulate door access, by creating a new entry
        device = AccessDevice()
        device.save()
        logentry = DeviceAccessLogEntry()
        logentry.payload = "1234567"
        logentry.device = device
        logentry.granted = False
        logentry.save()

        response = self.client.get(
            reverse("usersettings", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertEqual(len(response.context["unclaimed_nfccards"]), 1)

        # claim it
        response = self.client.post(
            reverse("usersettings_claim_nfc", args=(self.user.id,)),
            {"logentryid": logentry.id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # the code is not found from the page anymore
        self.assertNotContains(response, logentry.payload)
        # got success message
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "NFC Card successfully claimed")
        # and the card censored id can be found
        self.user.refresh_from_db()
        cardcensoredid = self.user.nfccard_set.first().censored_id()
        self.assertContains(response, cardcensoredid)
        # and nothing in claims anymore
        self.assertNotContains(
            response,
            "No recent unclaimed NFC cards. Go to door, use a card and claim it here in 5 minutes",
        )

        # delete it
        response = self.client.post(
            reverse("usersettings_delete_nfc", args=(self.user.id,)),
            {"nfccardid": self.user.nfccard_set.first().id},
            follow=True,
            HTTP_ACCEPT_LANGUAGE="en",
        )
        # got success message
        messages = list(response.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "NFC Card successfully deleted")
        # and the card censored id can be found
        self.assertNotContains(response, cardcensoredid)
        # and nothing to claim
        self.assertContains(
            response,
            "No recent unclaimed NFC cards. Go to door, use a card and claim it here in 5 minutes",
        )

        # check that our log has the entries
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(
            response,
            f"Registered new NFC card {cardcensoredid}",
        )
        self.assertContains(
            response,
            f"Deleted NFC card {cardcensoredid}",
        )

    def tearDown(self):
        get_user_model().objects.all().delete()
