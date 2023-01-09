import logging
import time

from django import forms
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str

logger = logging.getLogger(__name__)


class EmailActionForm(forms.Form):
    """send the email"""

    def save(self, email, adminuser):
        start = time.time()
        LogEntry.objects.log_action(
            user_id=adminuser.pk,
            content_type_id=ContentType.objects.get_for_model(email).pk,
            object_id=email.pk,
            object_repr=force_str(email),
            action_flag=CHANGE,
            change_message="Start queuing",
        )

        email.queue_to_recipients(get_user_model().objects.filter(is_active=True))

        end = time.time()
        elapsed = end - start
        LogEntry.objects.log_action(
            user_id=adminuser.pk,
            content_type_id=ContentType.objects.get_for_model(email).pk,
            object_id=email.pk,
            object_repr=force_str(email),
            action_flag=CHANGE,
            change_message=f"Queuing done, sending took {elapsed}",
        )
