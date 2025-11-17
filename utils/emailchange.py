from django.core import signing
import django.urls as urls
from django.utils.translation import gettext as _
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from drfx import config

EMAIL_CHANGE_SALT = "users.email-change-v1"
TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24  # 24 hours


def make_email_change_token(user, new_email, old_email):
    payload = {
        "uid": user.pk,
        "new_email": new_email,
        "old_email": old_email,
    }
    return signing.dumps(payload, salt=EMAIL_CHANGE_SALT)


def unsign_email_change_token(token, max_age=TOKEN_MAX_AGE_SECONDS):
    data = signing.loads(token, salt=EMAIL_CHANGE_SALT, max_age=max_age)
    return data


def send_email_change_confirmation(request, user, new_email, old_email):
    token = make_email_change_token(user, new_email, old_email)
    confirm_url = request.build_absolute_uri(
        urls.reverse("confirm_email_change", args=[token])
    )
    context = {
        "user": user,
        "confirm_url": confirm_url,
        "site": Site.objects.get_current(),
    }

    subject = _("Confirm your email change")
    content = render_to_string("mail/confirm_email_change.txt", context)

    send_mail(subject, content, config.NOREPLY_FROM_ADDRESS, [new_email])
