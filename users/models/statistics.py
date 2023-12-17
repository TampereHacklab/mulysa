import logging

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from datetime import datetime
from . import MembershipApplication, CustomInvoice, MemberService

from django.db.models import Sum, Count, Q

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
        subscriptions = (
            MemberService.objects.all()
            .values("pk", "name")
            .annotate(
                total=Count("pk"),
                active=Count(
                    "servicesubscription", filter=Q(servicesubscription__state="ACTIVE")
                ),
                overdue=Count(
                    "servicesubscription",
                    filter=Q(servicesubscription__state="OVERDUE"),
                ),
                suspended=Count(
                    "servicesubscription",
                    filter=Q(servicesubscription__state="SUSPENDED"),
                ),
            )
        )

        # collect service data for each different state
        self.update_or_create(
            date=datetime.now().date(),
            defaults={
                "users_total": get_user_model().objects.all().count(),
                "users_active": get_user_model().objects.filter(is_active=1).count(),
                "users_marked_for_deletion": get_user_model()
                .objects.filter(marked_for_deletion_on__isnull=False)
                .count(),
                "open_membership_applications": MembershipApplication.objects.all().count(),
                "custom_invoices_open": CustomInvoice.objects.filter(
                    payment_transaction=None
                ).count(),
                "custom_invoices_open_sum": CustomInvoice.objects.filter(
                    payment_transaction=None
                ).aggregate(total=Sum("amount", default=0))["total"],
                "service_subscriptions": list(subscriptions),
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
        verbose_name=_("Date of this statistics event"),
    )
    users_total = models.IntegerField(
        default=0, verbose_name=_("Total number of users")
    )
    users_active = models.IntegerField(default=0, verbose_name=_("Active users"))
    users_marked_for_deletion = models.IntegerField(
        default=0, verbose_name=_("Users pending deletion")
    )

    open_membership_applications = models.IntegerField(
        default=0, verbose_name=_("Number of open membership applications")
    )

    custom_invoices_open = models.IntegerField(
        default=0, verbose_name=_("Number of open custom invoices")
    )
    custom_invoices_open_sum = models.FloatField(
        default=0, verbose_name=_("Total amount of open custom invoices")
    )

    service_subscriptions = models.JSONField(
        default=list,
        verbose_name=_(
            "Statistics for service subscriptions. Each service will be its own key with counts for Active, Overdue and Suspended states"
        ),
    )

    def __str__(self):
        return f"Statistics for {self.date}"
