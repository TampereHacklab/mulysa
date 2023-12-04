import datetime
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from mailer.models import Message
from rest_framework import status
from rest_framework.test import APITestCase

from utils.businesslogic import BusinessLogic

from . import models, signals
from django.contrib.sites.models import Site
from drfx import config


class TestBusinessLogicSubscriptionExpiries(TestCase):
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
        self.user2 = get_user_model().objects.create_customuser(
            first_name="FirstName2",
            last_name="LastName2",
            email="user2@example.com",
            birthday=timezone.now(),
            municipality="City2",
            nick="user2",
            phone="+358123124",
        )

        # this should be found
        self.memberservice = models.MemberService.objects.create(
            name="TestService", cost=10, days_per_payment=30, days_before_warning=2
        )
        self.servicesubscription = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.ACTIVE,
            paid_until=timezone.now().date() + timedelta(days=2),
        )

        # this is found also another user
        self.servicesubscription_user2 = models.ServiceSubscription.objects.create(
            user=self.user2,
            service=self.memberservice,
            state=models.ServiceSubscription.ACTIVE,
            paid_until=timezone.now().date() + timedelta(days=2),
        )

        # and one more service
        self.memberservice3 = models.MemberService.objects.create(
            name="TestService3", cost=10, days_per_payment=30, days_before_warning=5
        )
        # this should also be found
        self.servicesubscription_user2_another = (
            models.ServiceSubscription.objects.create(
                user=self.user2,
                service=self.memberservice3,
                state=models.ServiceSubscription.ACTIVE,
                paid_until=timezone.now().date() + timedelta(days=5),
            )
        )
        # but this should not be found
        self.servicesubscription_user2_another2 = (
            models.ServiceSubscription.objects.create(
                user=self.user2,
                service=self.memberservice3,
                state=models.ServiceSubscription.ACTIVE,
                paid_until=timezone.now().date() + timedelta(days=3),
            )
        )

        # this service should never be found (no days_before_warning defined)
        self.memberservice2 = models.MemberService.objects.create(
            name="TestService2", cost=10, days_per_payment=30, days_before_warning=None
        )
        self.servicesubscription2 = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice2,
            state=models.ServiceSubscription.ACTIVE,
            paid_until=timezone.now().date() + timedelta(days=2),
        )

        # this should not be found (too far in the future)
        # note if we ever constraint having only one subscription per user / memberservice
        # these test will fail and need to be rewritten
        self.servicesubscription3 = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.ACTIVE,
            paid_until=timezone.now().date() + timedelta(days=3),
        )

        # this should not be found (in the past already)
        self.servicesubscription4 = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.ACTIVE,
            paid_until=timezone.now().date() + timedelta(days=1),
        )

    def test_find(self):
        about_to_expire = BusinessLogic.find_expiring_service_subscriptions()
        self.assertEqual(len(about_to_expire), 3)
        self.assertEqual(
            list(about_to_expire),
            [
                self.servicesubscription,
                self.servicesubscription_user2,
                self.servicesubscription_user2_another,
            ],
        )

    def tearDown(self):
        models.ServiceSubscription.objects.all().delete()
        models.MemberService.objects.all().delete()
        get_user_model().objects.all().delete()


class TestExpiryNotificationEmail(TestCase):
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
        self.user.language = "fi"
        self.user.save()
        # this should be found
        self.memberservice = models.MemberService.objects.create(
            name="TestService", cost=10, days_per_payment=30, days_before_warning=2
        )
        self.servicesubscription = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.ACTIVE,
            paid_until=timezone.now().date() + timedelta(days=2),
        )

    def test_send_expiry_notification(self):
        # get qs to pass to notification sender, should only have one result
        about_to_expire = BusinessLogic.find_expiring_service_subscriptions()
        self.assertEqual(len(about_to_expire), 1)

        # queue the messages
        BusinessLogic.notify_expiring_service_subscriptions(about_to_expire)

        # one message queued
        self.assertEqual(len(Message.objects.all()), 1)
        # check that it contains somewhat valid data
        message = Message.objects.first()
        self.assertEqual(self.user.email, message.email.to[0])
        self.assertIn(self.servicesubscription.service.name, message.email.subject)
        self.assertIn(f"Hei {self.user.first_name}", message.email.body)
        self.assertIn(self.servicesubscription.service.name, message.email.body)
        self.assertIn(str(self.servicesubscription.paid_until.year), message.email.body)

    def tearDown(self):
        models.MemberService.objects.all().delete()
        models.ServiceSubscription.objects.all().delete()
        get_user_model().objects.all().delete()


class TestNewApplicationHappyPathEmails(TestCase):
    """
    Test that user gets a "thank you for registering" email
    and after the application has been approved test that they
    get a "welcome" email
    """

    def setUp(self):
        # test objects
        self.memberservice = models.MemberService.objects.create(
            name="TestService",
            access_phone_number="+358123",
            cost=321,
            days_per_payment=30,
        )
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        # be specific about the language to use for the test user
        self.user.language = "fi"
        self.user.save()
        self.ss = BusinessLogic.create_servicesubscription(
            self.user, self.memberservice, models.ServiceSubscription.SUSPENDED
        )

    def test_emails(self):
        mail.outbox = []

        site = Site.objects.get_current()
        # create new application for our user
        self.application = models.MembershipApplication.objects.create(
            user=self.user, agreement=True
        )
        self.assertEqual(
            len(mail.outbox), 2
        )  # because this sends one email to the member and one to admins
        self.assertIn("Kiitos jäsenhakemuksestasi", mail.outbox[0].body, "Thanks")
        self.assertIn(site.domain, mail.outbox[0].body, "siteurl")
        self.assertIn(config.MEMBERS_GUIDE_URL, mail.outbox[0].body, "wikiurl")

        # for completenes sake, check the admin email also
        self.assertIn("FirstName LastName", mail.outbox[1].body, "Admin notification")
        self.assertIn(site.domain, mail.outbox[1].body, "admin url")

        # empty mailbox for next test
        mail.outbox = []
        BusinessLogic.accept_application(self.application)
        self.assertEqual(
            len(mail.outbox), 1
        )  # because this sends one email to the member and one to admins
        self.assertIn(
            f"Tervetuloa jäseneksi {self.user.first_name}",
            mail.outbox[0].body,
            "Welcome",
        )
        self.assertIn(self.memberservice.name, mail.outbox[0].body, "service found")
        self.assertIn(
            str(self.ss.reference_number), mail.outbox[0].body, "reference number found"
        )
        self.assertIn(
            self.memberservice.access_phone_number,
            mail.outbox[0].body,
            "phone number found",
        )
        self.assertIn(site.domain, mail.outbox[0].body, "url")
        self.assertIn(config.MEMBERS_GUIDE_URL, mail.outbox[0].body, "wikiurl")


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
            state=models.ServiceSubscription.OVERDUE,
        )
        self.assertIsNotNone(ss.reference_number)
        self.assertIn(str(ss.id), str(ss.reference_number))

        # but we can still forcibly clear it
        ss.reference_number = None
        ss.save()
        ss.refresh_from_db()
        self.assertIsNone(ss.reference_number)

        # and set it to what ever we want
        ss.reference_number = "123"
        ss.save()
        ss.refresh_from_db()
        self.assertEqual(ss.reference_number, "123")

        # and if we create one with a specific number it wont be overwritten
        ss = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.OVERDUE,
            reference_number="999",
        )
        self.assertIsNotNone(ss.reference_number)
        self.assertEqual(ss.reference_number, "999")


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
        get users api call. unauthenticated users don't get anything
        """
        url = reverse("customuser-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)


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
            state=models.ServiceSubscription.OVERDUE,
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
        invoice.reference_number = "123"
        invoice.save()
        invoice.refresh_from_db()
        self.assertEqual(invoice.reference_number, "123")

        # and if we create one with a specific number it wont be overwritten
        invoice2 = models.CustomInvoice.objects.create(
            user=self.user,
            subscription=self.servicesubscription,
            amount=amount,
            days=days,
            reference_number="999",
        )
        self.assertIsNotNone(invoice2.reference_number)
        self.assertEqual(invoice2.reference_number, "999")

    def tearDown(self):
        models.CustomInvoice.objects.all().delete()
        models.CustomUser.objects.all().delete()
        models.MemberService.objects.all().delete()
        models.ServiceSubscription.objects.all().delete()


class BankAggreagetApiTests(APITestCase):
    def setUp(self):
        """
        Generate few banktransactions for testing
        """
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        # for these dates, generate 10 deposits and withdravals for each day
        start_date = date(2022, 1, 1)
        end_date = date(2022, 1, 11)
        for single_date in self.daterange(start_date, end_date):
            for amount in range(1, 11):
                models.BankTransaction.objects.create(
                    archival_reference=f"{single_date}_deposit_{amount}",
                    date=single_date,
                    amount=amount,
                )
                models.BankTransaction.objects.create(
                    archival_reference=f"{single_date}_withdraval_{amount}",
                    date=single_date,
                    amount=amount * -1,
                )

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def test_get_banktransactionaggregatedata_not_loggedin(self):
        """
        only logged in users can get the data
        """
        url = reverse("banktransactionaggregate-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_banktransactionaggregatedata(self):
        """
        aggregated data
        """
        self.client.force_login(user=self.user)
        url = reverse("banktransactionaggregate-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

        # check first day data
        firstDay = response.data[0]
        self.assertEqual(firstDay["withdrawals"], -55)
        self.assertEqual(firstDay["deposits"], 55)
        self.assertEqual(firstDay["deposits"] + firstDay["withdrawals"], 0)
        self.assertEqual(firstDay["aggregatedate"], "2022-01-01")

        # last day data is similar
        lastDay = response.data[-1]
        self.assertEqual(lastDay["withdrawals"], -55)
        self.assertEqual(lastDay["deposits"], 55)
        self.assertEqual(lastDay["deposits"] + lastDay["withdrawals"], 0)
        self.assertEqual(lastDay["aggregatedate"], "2022-01-10")

    def test_get_banktransactionaggregatedata_filtered(self):
        """
        aggregated data
        """
        self.client.force_login(user=self.user)
        urlbase = reverse("banktransactionaggregate-list")
        qparams = urlencode({"date__gte": "2022-01-01", "date__lte": "2022-01-01"})
        url = f"{urlbase}?{qparams}"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # only one day result
        self.assertEqual(len(response.data), 1)
        firstDay = response.data[0]
        self.assertEqual(firstDay["withdrawals"], -55)
        self.assertEqual(firstDay["deposits"], 55)
        self.assertEqual(firstDay["deposits"] + firstDay["withdrawals"], 0)
        self.assertEqual(firstDay["aggregatedate"], "2022-01-01")

    def tearDown(self):
        models.CustomUser.objects.all().delete()
        models.BankTransaction.objects.all().delete()
