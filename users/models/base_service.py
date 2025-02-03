from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

"""
Class that represents a service for members. For example:
 - Yearly membership
 - Access rights
"""


class BaseService(models.Model):

    name = models.CharField(
        verbose_name=_("Service name"),
        help_text=_("Name of the service"),
        max_length=512,
    )

    cost = models.IntegerField(
        verbose_name=_("Cost of the service"),
        validators=[MinValueValidator(0)],
    )

    # This can be used to make "private" services that need to be added by admin to user.
    # Can also be used for soft deletion
    hidden = models.BooleanField(
        blank=False,
        null=False,
        default=False,
        help_text=_(
            "True, if this service should not be shown for user member application form etc."
        ),
    )

    def __str__(self):
        return _("Base service") + " " + str(self.name)

    # Returns the cost of the service in human-readable string
    def cost_string(self):
        cs = str(self.cost) + "€ "
        return cs

    class Meta:
        abstract = True
