from django.db import models
from django.utils.translation import gettext_lazy as _

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

    def __str__(self):
        return _("Service %(servicename)s for %(username)s") % {
            "servicename": self.service.name,
            "username": str(self.user),
        }
