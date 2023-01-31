from django.db import models
from django.utils.translation import gettext_lazy as _

from users.models.custom_user import CustomUser


class NFCCard(models.Model):
    """
    NFC Card for user
    """

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    # some datetime bits
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Creation date"),
        help_text=_("Automatically set to now when is created"),
    )
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified datetime"),
        help_text=_("Last time this object was modified"),
    )
    cardid = models.CharField(
        blank=False,
        null=True,
        unique=True,
        verbose_name=_("NFC card id number as read by the card reader"),
        help_text=_("Usually hex format"),
        max_length=255,
    )

    def censored_id(self):
        if len(self.cardid) < 2:
            return "**"
        out = "*" * (len(self.cardid) - 2)
        out = out + self.cardid[-2:]
        return out

    def __str__(self):
        return f"NFC access card for user {self.user}"
