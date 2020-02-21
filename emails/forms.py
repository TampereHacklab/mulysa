import logging
from datetime import datetime

from django import forms

logger = logging.getLogger(__name__)


class EmailActionForm(forms.Form):
    """ send the email """

    def save(self, email, user):
        email.sent = datetime.now()
        email.slug = email.slugify()
        email.save()
        logger.info("Sending email")
