from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from drfx import config

from .. import models


class TestUserDeletion(TestCase):
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

        self.memberservice = models.MemberService.objects.create(
            name="TestService", cost=10, days_per_payment=30, days_before_warning=2
        )

        mail.outbox = []

    def test_mark_user_for_deletion(self):
        """
        Test marking user for deletion
        """
        self.assertEqual(self.user.is_active, True)
        self.assertIsNone(self.user.marked_for_deletion_on)

        self.user.marked_for_deletion_on = timezone.now()
        self.user.save()

        # user was marked is inactive
        self.assertEqual(self.user.is_active, False)

        # email was sent to user and admins
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)
        self.assertIn(config.MEMBERSHIP_APPLICATION_NOTIFY_ADDRESS, mail.outbox[0].to)
        self.assertIn("Your account", mail.outbox[0].subject)
        self.assertIn("deletion", mail.outbox[0].body)
        self.assertIn(self.user.first_name, mail.outbox[0].body)

        # clear outbox
        mail.outbox = []

        # mark again
        self.user.marked_for_deletion_on = timezone.now()
        self.user.save()

        # no emails sent
        self.assertEqual(len(mail.outbox), 0)

        # clear again
        mail.outbox = []

        # remove mark
        self.user.marked_for_deletion_on = None
        self.user.save()

        # user still marked as inactive
        self.assertEqual(self.user.is_active, False)

        # no email notifications
        self.assertEqual(len(mail.outbox), 0)

    def test_user_deletion(self):
        """
        Check that all necessary (and just the necessary) objects are cleared when user is deleted
        """
        # add few objects pointing to this user, log entries, payment transactions, service subcsriptions
        self.subscription = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.ACTIVE,
            paid_until=timezone.now().date(),
        )

        # log entry for the user
        models.UsersLog.objects.create(user=self.user, message="test")

        # nfc card
        models.NFCCard.objects.create(user=self.user, cardid="123")

        # custom invoice
        models.CustomInvoice.objects.create(
            user=self.user,
            subscription=self.subscription,
            days=10,
            amount=10,
        )

        # bank transaction that points to the user
        self.transaction = models.BankTransaction.objects.create(
            user=self.user, date=timezone.now().date(), amount=10
        )

        # delete the user
        self.user.delete()

        # user was deleted
        self.assertEqual(models.CustomUser.objects.count(), 0)

        # the subscription was deleted
        self.assertEqual(models.ServiceSubscription.objects.count(), 0)

        # message log was deleted
        self.assertEqual(models.UsersLog.objects.count(), 0)

        # nfc card is removed
        self.assertEqual(models.NFCCard.objects.count(), 0)

        # custom invoice is removed
        self.assertEqual(models.CustomInvoice.objects.count(), 0)

        # bank transaction was not removed
        self.assertEqual(models.BankTransaction.objects.count(), 1)
        # but the user assignment is cleared
        self.transaction.refresh_from_db()
        self.assertEqual(self.transaction.user, None)

    def tearDown(self):
        mail.outbox = []
        get_user_model().objects.all().delete()
        models.MemberService.objects.all().delete()
