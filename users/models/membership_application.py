from django.utils import timezone
from django.db import models
from users.models.custom_user import CustomUser
from django.utils.translation import gettext_lazy as _

from users.validators import validate_agreement

"""
Extra fields for applying membership
"""


class MembershipApplication(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(
        blank=True,
        verbose_name=_("Message"),
        help_text=_("Free-form message to hacklab board"),
        max_length=1024,
    )

    # some datetime bits
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Application creation date"),
        help_text=_("Automatically set to now when membership application is created"),
    )

    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified datetime"),
        help_text=_("Last time this membership application was modified"),
    )

    def age_days(self):
        return (timezone.now() - self.created).days

    def __str__(self):
        return _("Membership application for %(name)s") % {"name": str(self.user)}
