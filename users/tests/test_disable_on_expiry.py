from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from datetime import date, timedelta

from utils import referencenumber
from utils.businesslogic import BusinessLogic
from users.models import BankTransaction, MemberService, ServiceSubscription


class DisableOnExpiryTests(TestCase):
    """
    Tests for the disable_on_expiry feature that allows subscriptions
    to be deleted instead of going overdue when paid days run out.
    """

    def setUp(self):
        """
        Set up test user and service
        """
        self.user = get_user_model().objects.create_customuser(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            birthday=date.today() - timedelta(days=365 * 25),
            municipality="TestCity",
            nick="testuser",
            phone="+358401234567",
        )

        self.service = MemberService(
            name="Test Access",
            cost=30,
            days_per_payment=30,
            days_bonus_for_first=0,
        )
        self.service.save()

        self.subscription = ServiceSubscription(
            user=self.user,
            service=self.service,
            state=ServiceSubscription.ACTIVE,
            paid_until=date.today() + timedelta(days=10),
            reference_number=referencenumber.generate(12345),
        )
        self.subscription.save()

    def test_subscription_deleted_when_expires_with_flag_set(self):
        """
        Test that subscription is deleted instead of going overdue
        when disable_on_expiry is True
        """
        # Set the disable_on_expiry flag
        self.subscription.disable_on_expiry = True
        self.subscription.save()

        # Set paid_until to the past
        self.subscription.paid_until = date.today() - timedelta(days=1)
        self.subscription.save()

        # Run the state check
        BusinessLogic._check_servicesubscription_state(self.subscription)

        # Subscription should be deleted
        self.assertFalse(
            ServiceSubscription.objects.filter(id=self.subscription.id).exists()
        )

    def test_disable_on_expiry_flag_cleared_on_payment(self):
        """
        Test that disable_on_expiry flag is cleared when user makes a payment
        """
        # Set the disable_on_expiry flag
        self.subscription.disable_on_expiry = True
        self.subscription.paid_until = date.today()
        self.subscription.save()

        # Create a payment transaction
        transaction = BankTransaction(
            user=self.user,
            amount=30,
            reference_number=self.subscription.reference_number,
            date=date.today(),
            archival_reference="TEST123",
            has_been_used=False,
        )
        transaction.save()

        # Process the payment
        BusinessLogic.updateuser(self.user)

        # Flag should be cleared
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.disable_on_expiry)

    def test_user_self_unsubscribe_sets_flag(self):
        """
        Test that when user clicks 'Unsubscribe service' button,
        the disable_on_expiry flag is set
        """
        # Make service self-subscribable
        self.service.self_subscribe = True
        self.service.save()

        # Ensure subscription is active and paid
        self.subscription.state = ServiceSubscription.ACTIVE
        self.subscription.paid_until = date.today() + timedelta(days=10)
        self.subscription.save()

        # Login as user
        self.client.force_login(self.user)

        # User clicks unsubscribe
        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            {"subscriptionid": self.subscription.id},
            follow=True,
        )

        # Check that flag was set
        self.subscription.refresh_from_db()
        self.assertTrue(self.subscription.disable_on_expiry)

        # Now cancel - toggle the same button
        response = self.client.post(
            reverse("usersettings_unsubscribe_service", args=(self.user.id,)),
            {"subscriptionid": self.subscription.id},
            follow=True,
        )

        # Check that flag was cleared
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.disable_on_expiry)

        # Check success message for cancel
        messages = list(response.context["messages"])
        # Message could be in English or Finnish (peruttu = cancelled)
        message_text = str(messages[0]).lower()
        self.assertTrue("cancel" in message_text or "peru" in message_text)
