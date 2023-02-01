from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_mxid(value):
    # Empty is ok
    if len(value) == 0:
        return

    if len(value) < 3 or value[0] != "@" or ":" not in value:
        raise ValidationError(
            _(
                "%(value)s is not a valid Matrix id. It must be in format @user:example.org"
            ),
            params={"value": value},
        )


def validate_phone(value):
    if len(value) < 3 or value[0] != "+" or not value[1:].isnumeric():
        raise ValidationError(
            _(
                "%(value)s is not a valid phone number. It must be in international format +35840123567"
            ),
            params={"value": value},
        )


def validate_agreement(value):
    if not value:
        raise ValidationError(_("You must agree to the terms"))
