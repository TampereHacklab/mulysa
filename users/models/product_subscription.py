from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

from users.models.bank_transaction import BankTransaction


class ProductSubscription(models.Model):
    """
    Represents user subscribing to a product.
    """

    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)

    start_date = models.DateField()

    # The price this subscription will pay for one instance of the product
    price = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Minimum payment",
        validators=[MinValueValidator(0)],  # FIXME: This should never be below the min_price of the product nor above the max_price of the product
    )

    def is_active(self):
        """
        helper method for checking if the service is active
        """
        # FIXME: Implement this
        return True

    def get_state(self):
        # FIXME: Implement this
        return "Some state base on the account balance and whatnot"

    # Return the translated name of the state
    def statestring(self):
        # FIXME
        return "(???)"

    # Return the estimated date the user (probably) will need to make a new payment to keep the subscription paid
    def next_payment_date(self):
        # FIXME
        return "01.01.2027"

    def __str__(self):
        return _("Subscription to %(product_name)s for %(username)s") % {
            "product_name": self.product.name,
            "username": str(self.user),
        }
