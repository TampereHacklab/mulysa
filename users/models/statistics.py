import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from datetime import datetime
from . import MembershipApplication, CustomInvoice

from django.db.models import Sum

logger = logging.getLogger(__name__)


class StatisticsManager(models.Manager):
    """
    Statistics manager, mainly for easy statistics collection with `take_daily_stats`

    TODO: maybe some helper methods for getting the data in a nice way too?
    """

    def collect_daily_stats(self):
        """
        Take new daily stats right now.

        If today already has a daily stat object will update the values for today.
        """
        self.update_or_create(
            date=datetime.now().date(),
            defaults={
                "users_total": get_user_model().objects.all().count(),
                "users_active": get_user_model().objects.filter(is_active=1).count(),
                "open_membership_applications": MembershipApplication.objects.all().count(),

                "custom_invoices_open": CustomInvoice.objects.filter(payment_transaction=None).count(),
                "custom_invoices_open_sum": CustomInvoice.objects.filter(payment_transaction=None).aggregate(total=Sum('amount'))['total'],
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

    open_membership_applications = models.IntegerField(verbose_name="Number of open membership applications")

    custom_invoices_open = models.IntegerField(verbose_name="Number of open custom invoices")
    custom_invoices_open_sum = models.FloatField(verbose_name="Total amount of open custom invoices")

    def __str__(self):
        return f"Statistics for {self.date}"
