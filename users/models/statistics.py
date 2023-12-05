import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class Statistics(models.Model):
    """
    Statistics information for one day
    """
    date = models.DateField(
        auto_now_add=True, verbose_name="Date of this statistics event"
    )

    total_users = models.IntegerField(
        verbose_name='How many users in total in the system'
    )
    active_users = models.IntegerField(
        verbose_name='How many active users in in the system'
    )
    open_member_applications = models.IntegerField(
        verbose_name='Number of open member applications'
    )


    def __str__(self):
        return f"{self.date}: Users={self.users}"
