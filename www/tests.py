from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import MemberService

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
            name="TestService",
            cost=10,
            days_per_payment=30,
            days_before_warning=2
        )

    def test_my_info(self):
        response = self.client.get(
            reverse("userdetails", args=(self.user.id,)), HTTP_ACCEPT_LANGUAGE="en"
        )
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)

        # no memberservices
        self.assertEqual(len(response.context['userdetails.servicesubscriptions']), 0)

    def tearDown(self):
        get_user_model().objects.all().delete()


class TestStaffVies(TestCase):
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
