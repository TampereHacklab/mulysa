from django.db import models
from django.utils.translation import gettext_lazy as _


class BankTransaction(models.Model):
    """
    Represents a incoming money transaction on the club's account.
    """
    # Unique archival reference number that all transactions have
    archival_reference = models.CharField(
        blank=False,
        null=False,
        unique=True,
        verbose_name=_("Archival reference"),
        max_length=32,
    )
    date = models.DateField(
        verbose_name=_("Date"),
        help_text=_("Date of the transaction"),
    )
    amount = models.DecimalField(
        verbose_name=_("Amount"),
        help_text=_("Amount of money transferred to account"),
        max_digits=6,
        decimal_places=2,
    )
    message = models.CharField(
        blank=True,
        verbose_name=_("Message"),
        help_text=_(
            "Message attached to transaction by sender. Should not normally be used."
        ),
        max_length=512,
    )
    sender = models.CharField(
        blank=True,
        null=True,
        verbose_name=_("Sender"),
        help_text=_("Sender of the transaction, if known."),
        max_length=512,
    )
    # https://en.wikipedia.org/wiki/Creditor_Reference#:~:text=The%20Creditor%20Reference%20is%20an,reference%20will%20be%20entered%20correctly.
    reference_number = models.CharField(
        blank=True,
        null=True,
        verbose_name=_("Transaction reference"),
        help_text=_(
            "Reference number is set by transaction sender and should normally always be used."
        ),
        max_length=25,
    )
    transaction_id = models.CharField(
        blank=True,
        null=True,
        verbose_name=_("Transaction id"),
        help_text=_("Bank transaction id"),
        max_length=512,
    )
    code = models.CharField(
        blank=True,
        null=True,
        verbose_name=_("Code"),
        help_text=_("Code"),
        max_length=512,
    )

    comment = models.TextField(
        blank=True,
        null=True,
        help_text=_("free form comment field for strange transaction"),
    )

    def __str__(self):
        return (
            f'Bank transaction for {(self.user and self.user.email) or "unknown user"}'
            + f" from {self.sender}"
            + f" {self.amount}€, reference {self.reference_number}"
            + ((", message " + self.message) if self.message else "")
            + f' at {self.date or "(no date)"}'
        )
