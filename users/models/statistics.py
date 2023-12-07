import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from datetime import datetime

logger = logging.getLogger(__name__)


class StatisticsManager(models.Manager):
    """
    Statistics manager, mainly for easy statistics collection with `take_daily_stats`

    TODO: maybe some helper methods for getting the data in a nice way too?
    """

    def take_daily_stats(self):
        """
        Take new daily stats right now.

        If today already has a daily stat object will update the values for today.
        """
        self.update_or_create(
            date=datetime.now().date(),
            defaults={
                "users_total": get_user_model().objects.all().count(),
                "users_active": get_user_model().objects.filter(is_active=1).count(),
            },
        )


class Statistics(models.Model):
    """
    Statistics information for one day
    """

    objects = StatisticsManager()

    date = models.DateField(
        auto_now_add=True,
        unique=True,
        primary_key=True,
        verbose_name="Date of this statistics event",
    )
    users_total = models.IntegerField(verbose_name="Total number of users")
    users_active = models.IntegerField(verbose_name="Active users")

    def __str__(self):
        return f"Statistics for {self.date}"
