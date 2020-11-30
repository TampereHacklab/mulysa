import datetime
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone


class IndexViewTestsNotLoggedIn(TestCase):
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

    def test_index_logged(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="en")
        self.assertContains(response, "Welcome back")
        response = self.client.get(reverse("index"), HTTP_ACCEPT_LANGUAGE="fi")
        self.assertContains(response, "Tervetuloa takaisin")

    def tearDown(self):
        get_user_model().objects.all().delete()
