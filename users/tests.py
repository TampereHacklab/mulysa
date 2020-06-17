import datetime

from django.contrib.auth import get_user_model
from django.core import mail
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from . import models, signals


class ServiceSubscriptionTests(TestCase):
    def setUp(self):
        # one active user, one inactive user
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.memberservice = models.MemberService.objects.create(
            name="TestService",
            cost=10,
            days_per_payment=30,
        )

    def test_automagic_reference_number(self):
        # create will generate reference number for us
        ss = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.OVERDUE
        )
        self.assertIsNotNone(ss.reference_number)
        self.assertIn(str(ss.id), str(ss.reference_number))

        # but we can still forcibly clear it
        ss.reference_number = None
        ss.save()
        ss.refresh_from_db()
        self.assertIsNone(ss.reference_number)

        # and set it to what ever we want
        ss.reference_number = 123
        ss.save()
        ss.refresh_from_db()
        self.assertEqual(ss.reference_number, 123)

        # and if we create one with a specific number it wont be overwritten
        ss = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.OVERDUE,
            reference_number=999
        )
        self.assertIsNotNone(ss.reference_number)
        self.assertEqual(ss.reference_number, 999)


class UserManagerTests(APITestCase):
    def test_create_superuser(self):
        models.CustomUser.objects.create_superuser(
            email="testsuper@example.com",
            first_name="test",
            last_name="super",
            phone="123123",
            password="abc123",
        )
        self.assertIsNotNone(
            models.CustomUser.objects.get(email="testsuper@example.com")
        )


class UsersTests(APITestCase):
    def test_create_user_invalid(self):
        # note, if your test generates exceptions it will brake the transaction
        # https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
        u = models.CustomUser()
        # cannot save without data
        with self.assertRaises(IntegrityError):
            u.save()

    def test_create_user(self):
        """
        Basic model testing
        """
        u = models.CustomUser()
        u.email = "test@example.com"
        u.birthday = datetime.datetime.now()
        u.first_name = "FirstName"
        u.last_name = "LastName"
        u.save()

        # check that the reset password email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            "www/reset/MQ/", mail.outbox[0].body, "link to reset found in email"
        )

        # for completenes sake
        self.assertEqual(u.email, u.get_short_name())
        self.assertEqual(u.email, u.natural_key())

    def test_signals(self):
        u = models.CustomUser()
        u.email = "signaltest@example.com"
        u.birthday = datetime.datetime.now()
        u.save()

        self.activate_call_counter = 0
        self.activate_instance_id = None

        self.deactivate_call_counter = 0
        self.deactivate_instance_id = None

        self.assertTrue(u.is_active, "user is active")

        # dummy listeners
        @receiver(signals.deactivate_user, sender=models.CustomUser)
        def dummy_activate_listener(sender, instance: models.CustomUser, **kwargs):
            self.activate_instance_id = instance.id
            self.activate_call_counter += 1

        @receiver(signals.deactivate_user, sender=models.CustomUser)
        def dummy_deactivate_listener(sender, instance: models.CustomUser, **kwargs):
            self.deactivate_instance_id = instance.id
            self.deactivate_call_counter += 1

        # deactivation triggers signal
        u.is_active = False
        u.save()

        # user activation triggers signal
        u.is_active = True
        u.save()

        # and check that our receivers were called
        self.assertEqual(
            self.activate_call_counter, 1, "activate signal was called once"
        )
        self.assertEqual(
            self.deactivate_call_counter, 1, "deactivate signal was called once"
        )
        self.assertEqual(u.id, self.activate_instance_id, "signal instance id matches")
        self.assertEqual(
            u.id, self.deactivate_instance_id, "signal instance id matches"
        )


class UsersAPITests(APITestCase):
    def test_get_users(self):
        """
        get users api call
        """
        url = reverse("customuser-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CustomInvoiceTests(TestCase):
    def setUp(self):
        # one active user, one inactive user
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.memberservice = models.MemberService.objects.create(
            name="TestService",
            cost=10,
            days_per_payment=30,
        )
        self.servicesubscription = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.OVERDUE
        )

    def test_automagic_reference_number(self):
        # add new custominvoice, it should get a referencenumber automagically
        days = 10
        amount = self.servicesubscription.service.cost * days
        invoice = models.CustomInvoice.objects.create(
            user=self.user,
            subscription=self.servicesubscription,
            amount=amount,
            days=days,
        )

        self.assertIsNotNone(invoice.reference_number)
        self.assertIn(str(invoice.id), str(invoice.reference_number))

        # but we can still forcibly clear it
        invoice.reference_number = None
        invoice.save()
        invoice.refresh_from_db()
        self.assertIsNone(invoice.reference_number)

        # and set it to what ever we want
        invoice.reference_number = 123
        invoice.save()
        invoice.refresh_from_db()
        self.assertEqual(invoice.reference_number, 123)

        # and if we create one with a specific number it wont be overwritten
        invoice2 = models.CustomInvoice.objects.create(
            user=self.user,
            subscription=self.servicesubscription,
            amount=amount,
            days=days,
            reference_number=999,
        )
        self.assertIsNotNone(invoice2.reference_number)
        self.assertEqual(invoice2.reference_number, 999)

    def tearDown(self):
        models.CustomInvoice.objects.all().delete()
        models.CustomUser.objects.all().delete()
        models.MemberService.objects.all().delete()
        models.ServiceSubscription.objects.all().delete()
