from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from users.models import MemberService, ServiceSubscription


class RequiredServiceSubscribabilityTests(TestCase):
    def setUp(self):
        self.client = self.client
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        # ensure we're authenticated as this user when calling the view
        self.client.force_login(self.user)

    def test_dependent_service_requires_active_prerequisite(self):
        # prerequisite service
        prereq = MemberService.objects.create(
            name="Prerequisite Service",
            cost=10,
            days_per_payment=30,
        )

        # dependent service that requires the prerequisite to be active
        dependent = MemberService.objects.create(
            name="Dependent Service",
            cost=5,
            days_per_payment=30,
            self_subscribe=True,
            required_service=prereq,
        )

        url = reverse("usersettings", args=(self.user.id,))

        # initially user has no subscriptions, so dependent service should NOT be shown
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        subscribable = list(response.context["subscribable_services"])
        self.assertNotIn(dependent, subscribable)

        # give user an ACTIVE subscription to the prerequisite
        ServiceSubscription.objects.create(
            user=self.user,
            service=prereq,
            state=ServiceSubscription.ACTIVE,
            reference_number="TEST-PREREQ-1",
        )

        # now the dependent service should appear in subscribable services
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        subscribable = list(response.context["subscribable_services"])
        self.assertIn(dependent, subscribable)
