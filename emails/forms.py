import logging
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailActionForm(forms.Form):
    """ send the email """

    def save(self, email, adminuser):
        email.sent = datetime.now()
        email.slug = email.slugify()

        LogEntry.objects.log_action(
            user_id=adminuser.pk,
            content_type_id=ContentType.objects.get_for_model(email).pk,
            object_id=email.pk,
            object_repr=force_text(email),
            action_flag=CHANGE,
            change_message=f"Start sending",
        )

        # send the email to all active users
        # TODO: the recipient set should be a setting
        # and the sending should happen in a queue
        for user in get_user_model().objects.filter(is_active=True):
            logger.info(
                "Sending email {email.subject} to {user.email}".format(
                    user=user, email=email
                )
            )

            context = {
                "user": user,
                "settings": settings,
                "email": email,
                "SITENAME": settings.SITENAME,
                "SITE_URL": settings.SITE_URL,
            }
            subject = email.subject
            from_email = settings.NOREPLY_FROM_ADDRESS
            to = user.email
            html_content = render_to_string("mail/email.html", context)
            plaintext_content = strip_tags(html_content)

            send_mail(
                subject, plaintext_content, from_email, [to], html_message=html_content
            )

            # log it
            LogEntry.objects.log_action(
                user_id=adminuser.pk,
                content_type_id=ContentType.objects.get_for_model(email).pk,
                object_id=email.pk,
                object_repr=force_text(email),
                action_flag=CHANGE,
                change_message=f"Sent to {user.email}",
            )

        # save the slug
        email.save()

        LogEntry.objects.log_action(
            user_id=adminuser.pk,
            content_type_id=ContentType.objects.get_for_model(email).pk,
            object_id=email.pk,
            object_repr=force_text(email),
            action_flag=CHANGE,
            change_message=f"Sending done",
        )

        logger.info("Sending email")
