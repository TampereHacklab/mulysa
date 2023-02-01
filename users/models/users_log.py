from django.db import models
from django.utils.translation import gettext_lazy as _


class UsersLog(models.Model):
    """
    A text log message for user activities (status changes, payments, etc)
    """

    # User this log message is associated with
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
    date = models.DateTimeField(
        auto_now_add=True, verbose_name="Date of this log event"
    )
    message = models.CharField(
        blank=False,
        verbose_name=_("Message"),
        max_length=1024,
    )

    def __str__(self):
        return f"{self.user} - {self.date}: {self.message}"
