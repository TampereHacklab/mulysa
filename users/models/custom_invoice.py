from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models.bank_transaction import BankTransaction

from users.models.custom_user import CustomUser
from users.models.service_subscription import ServiceSubscription


class CustomInvoice(models.Model):
    """
    Single invoice that can be used to pay for N units of service
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subscription = models.ForeignKey(ServiceSubscription, on_delete=models.CASCADE)
    days = models.IntegerField(
        blank=False,
        null=False,
        verbose_name=_("How many days of service this invoice pays"),
        help_text=_(
            "For example value 14 with access right service pays two weeks of access."
        ),
    )
    # https://en.wikipedia.org/wiki/Creditor_Reference#:~:text=The%20Creditor%20Reference%20is%20an,reference%20will%20be%20entered%20correctly.
    reference_number = models.CharField(
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Reference number for paying invoice"),
        help_text=_(
            "Reference number is set by transaction sender and must match this."
        ),
        max_length=25,
    )
    amount = models.DecimalField(
        verbose_name=_("Amount"),
        help_text=_("Minimum amount of money to satisfy this invoice."),
        max_digits=6,
        decimal_places=2,
    )
    # some datetime bits
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Invoice creation date"),
        help_text=_("Automatically set to now when invoice is created"),
    )
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified datetime"),
        help_text=_("Last time this invoice was modified"),
    )

    # Points to the payment, if this invoice has been paid.
    payment_transaction = models.ForeignKey(
        BankTransaction, on_delete=models.SET_NULL, blank=True, null=True
    )

    def __str__(self):
        return _(
            "Custom invoice to pay %(days)s days of %(servicename)s for %(username)s - %(amount)s€, reference: %(reference)s"
        ) % {
            "days": self.days,
            "servicename": self.subscription.service.name,
            "username": str(self.user),
            "amount": self.amount,
            "reference": self.reference_number,
        }
