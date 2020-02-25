from django.db import models
from django.utils.translation import ugettext_lazy as _

from autoslug import AutoSlugField


class Email(models.Model):
    """
    Email to be sent to users
    """

    subject = models.CharField(
        blank=False,
        null=False,
        verbose_name=_("Subject"),
        help_text=_(
            "Descriptive subject for the email. Finnish / English both should be written here"
        ),
        max_length=512,
    )

    slug = AutoSlugField(populate_from='subject', unique=True)

    content = models.TextField(
        blank=False,
        null=False,
        verbose_name=_("Content"),
        help_text=_(
            "Content of the email. All emails will start with default 'View this message in browser' and end with 'You are receiving this message because') texts"
        ),
    )

    # some datetime bits
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Creation date"),)

    last_modified = models.DateTimeField(
        auto_now=True, verbose_name=_("Last modified datetime"),
    )

    sent = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Datetime the message was sent")
    )

    def get_url(self):
        return f"{self.sent.strftime('%s')}/{self.slug}"

    def get_epoch(self):
        if(self.sent):
            return self.sent.strftime('%s')
        return '000'

    def __str__(self):
        return self.subject
