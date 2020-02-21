import logging

from django import forms

logger = logging.getLogger(__name__)


class EmailActionForm(forms.Form):
    """ send the email """

    def save(self, email, user):
        logger.info("Sending email")

