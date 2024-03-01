from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


"""
Class that represents a service for members. For example:
 - Yearly membership
 - Access rights
"""


class MemberService(models.Model):
    name = models.CharField(
        verbose_name=_("Service name"),
        help_text=_("Name of the service"),
        max_length=512,
    )

    cost = models.IntegerField(
        verbose_name="Normal cost of the service",
        validators=[MinValueValidator(0)],
    )

    days_per_payment = models.IntegerField(
        verbose_name="How many days of service member gets for a valid payment",
        validators=[MinValueValidator(0)],
    )

    # This can be used to make "private" services that need to be added by admin to user.
    hidden = models.BooleanField(
        blank=False,
        null=False,
        default=False,
        help_text=_(
            "True, if this service should not be shown for user member application form etc."
        ),
    )

    # True if users are allowed to subscribe and unsubscribe themselves with this service
    self_subscribe = models.BooleanField(
        blank=False,
        null=False,
        default=False,
        help_text=_(
            "True, if this service can be subscribed and unsubscribed by users themselves."
        ),
    )

    # for accounting
    accounting_id = models.CharField(
        max_length=20, blank=True, null=True, help_text=_("For accounting export")
    )

    def __str__(self):
        return _("Member service") + " " + str(self.name)

    # Returns the cost of the service in human-readable string
    def cost_string(self):
        cs = str(self.cost) + "€ "
        if self.cost_min and not self.cost_max:
            cs = cs + "(" + str(self.cost_min) + "€ min)"
        if not self.cost_min and self.cost_max:
            cs = cs + "(" + str(self.cost_max) + "€ max)"
        if self.cost_min and self.cost_max:
            cs = cs + "(" + str(self.cost_min) + "€ - " + str(self.cost_max) + "€)"
        return cs

    # Returns the period (days per payment) for the service in human-readable string
    def period_string(self):
        if self.days_per_payment == 31:
            return _("month")
        if self.days_per_payment == 365:
            return _("year")
        return str(self.days_per_payment) + " " + str(_("days"))
