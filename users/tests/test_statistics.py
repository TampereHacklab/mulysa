from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from rest_framework.test import APITestCase

from users import models


class StatisticsTests(APITestCase):
    """
    Tests for statistics data
    """

    def test_take_statistics_empty_db(self):
        """
        Statistics on basically an empty database
        """
        self.assertEqual(models.Statistics.objects.count(), 0)
        models.Statistics.objects.collect_daily_stats()
        models.Statistics.objects.collect_daily_stats()
        self.assertEqual(models.Statistics.objects.count(), 1)
        s = models.Statistics.objects.first()
        self.assertEqual(s.users_active, 0)
        self.assertEqual(s.users_total, 0)
        self.assertEqual(s.service_subscriptions, [])

    def test_take_statistics(self):
        """
        Build some data and take statistics again
        """
        models.Statistics.objects.all().delete()
        self.assertEqual(models.Statistics.objects.count(), 0)
        # take empty statistics first so we also test updating
        models.Statistics.objects.collect_daily_stats()
        self.assertEqual(models.Statistics.objects.count(), 1)
        s = models.Statistics.objects.first()
        self.assertEqual(s.users_total, 0)

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
        self.servicesubscription = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.ACTIVE,
            paid_until=timezone.now().date() + timedelta(days=2),
        )
        # this should update our existing and not create a new line
        models.Statistics.objects.collect_daily_stats()
        self.assertEqual(models.Statistics.objects.count(), 1)

        s.refresh_from_db()
        self.assertEqual(s.users_total, 1)
        self.assertEqual(len(s.service_subscriptions), 1)
        self.assertDictContainsSubset({"active": 1}, s.service_subscriptions[0])

    def tearDown(self):
        models.Statistics.objects.all().delete()
