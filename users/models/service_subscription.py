from django.db import models
from django.utils.translation import gettext_lazy as _
import datetime
from users.models.bank_transaction import BankTransaction


class ServiceSubscription(models.Model):
    """
    Represents user subscribing to a paid service.
    """

    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    service = models.ForeignKey("MemberService", on_delete=models.CASCADE)

    #   Service states:
    # Service is active, paid_until > current_date
    ACTIVE = "ACTIVE"
    # Service suspended, user must contact administration to continue.
    # This is used for example if a member wants to pause paying for
    # certain time due to travel or other reason.
    # Also the initial state before membership is approved.
    #
    # Note: service must be paid fully until moving to suspended state.
    SUSPENDED = "SUSPENDED"
    # Payment overdue, user must pay to activate service
    OVERDUE = "OVERDUE"

    SERVICE_STATES = [
        (ACTIVE, _("Active")),
        (OVERDUE, _("Payment overdue")),
        (SUSPENDED, _("Suspended")),
    ]

    state = models.CharField(
        blank=False,
        verbose_name=_("Service state"),
        help_text=_("State of this service"),
        max_length=16,
        choices=SERVICE_STATES,
        default=SUSPENDED,
    )

    # The important paid until date. If this is not set, service has not been used yet or
    # has been suspended.
    paid_until = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Paid until"),
        help_text=_("The service will stay active until this date"),
    )

    # Points to the latest payment that caused paid_until to update
    last_payment = models.ForeignKey(
        BankTransaction, on_delete=models.SET_NULL, blank=True, null=True
    )

    # https://en.wikipedia.org/wiki/Creditor_Reference#:~:text=The%20Creditor%20Reference%20is%20an,reference%20will%20be%20entered%20correctly.
    reference_number = models.CharField(
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Reference number for paying for this service subscription"),
        help_text=_("Pay for this service with this reference number"),
        max_length=25,
    )

    reminder_sent = models.DateField(
        blank=True,
        null=True,
        help_text=_(
            "Set date when a expiration reminder message has been sent to user. Reset to NULL when state changes."
        ),
    )

    SERVICE_STATE_COLORS = {
        ACTIVE: "green",
        OVERDUE: "yellow",
        SUSPENDED: "red",
    }

    def is_active(self):
        """
        helper method for checking if the service is active
        """
        return True if self.state == ServiceSubscription.ACTIVE else False

    # Convenince method to get color of the state for ui
    def statecolor(self):
        return self.SERVICE_STATE_COLORS[self.state]

    # Return the translated name of the state
    def statestring(self):
        # There's probably a one-liner way to do this
        for ss in ServiceSubscription.SERVICE_STATES:
            if ss[0] == self.state:
                return ss[1]
        return "(???)"  # Should never happen

    # Return number of days left until subscription ends
    def days_left(self):
        if self.state != ServiceSubscription.ACTIVE:
            return 0

        if not self.paid_until:  # Should be, but just to be sure
            return 0

        daysleft = (self.paid_until - datetime.date.today()).days
        if daysleft < 0:
            daysleft = 0
        return daysleft

    # Return number of days subscription is overdue
    def days_overdue(self):
        if self.state != ServiceSubscription.OVERDUE:
            return 0

        if not self.paid_until:
            return 0

        days_overdue = -(self.paid_until - datetime.date.today()).days
        if days_overdue < 0:
            days_overdue = 0
        return days_overdue

    # Returns a list of user's servicesubscriptions that pay for this subscription
    def paid_by_subscriptions(self):
        paying_subs = []
        paying_services = self.service.paid_by_services()
        for service in paying_services:
            subs = ServiceSubscription.objects.filter(user=self.user, service=service)
            if subs:
                paying_subs.append(subs[0].service.name)
        return paying_subs

    def __str__(self):
        return _("Service %(servicename)s for %(username)s") % {
            "servicename": self.service.name,
            "username": str(self.user),
        }
