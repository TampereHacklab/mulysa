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

    """
    Defines another service that this this service pays for. If this service is paid, the referenced
    service is also marked as paid for days_per_payment after the payment date.

    Can be used to make service chains so that if a more expensive
    service is paid, the user can automatically receive cheaper ones.
    """
    pays_also_service = models.ForeignKey(
        "self", on_delete=models.SET_NULL, blank=True, null=True
    )

    # cost is used if not set
    cost_min = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Minimum payment",
        validators=[MinValueValidator(0)],
    )

    # Can be left out if no maximum needed
    cost_max = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Maximum payment",
        validators=[MinValueValidator(0)],
    )

    days_per_payment = models.IntegerField(
        verbose_name="How many days of service member gets for a valid payment",
        validators=[MinValueValidator(0)],
    )

    days_bonus_for_first = models.IntegerField(
        default=0,
        verbose_name="How many extra days of service member gets when paying for first time",
        validators=[MinValueValidator(0)],
    )

    days_before_warning = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="How many days before payment expiration a warning message shall be sent",
        validators=[MinValueValidator(0)],
    )

    days_maximum = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="How many days of service member can pay at maximum",
        validators=[MinValueValidator(0)],
    )

    days_until_suspending = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="How many days service can be in payment pending state until it is moved to suspended state",
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

    access_phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Phone number that can be used to use this memberservice"),
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

    # Returns a list of services that pay for this service
    def paid_by_services(self):
        return MemberService.objects.filter(pays_also_service=self)
