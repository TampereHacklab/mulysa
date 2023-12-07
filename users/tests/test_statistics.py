from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from rest_framework import status
from rest_framework.test import APITestCase

from users.models import Statistics


class StatisticsTests(APITestCase):
    """
    Tests for statistics data
    """

    def test_take_statistics(self):
        self.assertEqual(Statistics.objects.count(), 0)
        Statistics.objects.collect_daily_stats()
        self.assertEqual(Statistics.objects.count(), 1)

    def tearDown(self):
        Statistics.objects.all().delete()
