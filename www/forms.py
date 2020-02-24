from datetime import datetime

from django import forms
from django.utils.translation import gettext as _

from users import models
from users.models import MemberService, ServiceSubscription
from django.db.utils import OperationalError


class RegistrationUserForm(forms.ModelForm):
    class Meta:
        model = models.CustomUser
        fields = [
            "first_name",
            "last_name",
            "email",
            "language",
            "municipality",
            "nick",
            "mxid",
            "birthday",
            "phone",
        ]
        localized_fields = ("birthday",)
        widgets = {
            "birthday": forms.SelectDateWidget(
                years=[
                    x
                    for x in range(
                        datetime.today().year - 100, datetime.today().year + 1
                    )
                ]
            )
        }


class RegistrationApplicationForm(forms.ModelForm):
    class Meta:
        model = models.MembershipApplication
        fields = ["message", "agreement"]


class RegistrationServicesFrom(forms.Form):
    def build_service_choices():
        """
        Helper for building service choices for the form
        """
        service_choices = []
        try:
            for service in MemberService.objects.all():
                name = _(service.name)
                service_choices.append(
                    (
                        service.pk,
                        f"{name}, {service.cost_string()} / {service.period_string()}",
                    )
                )
        except OperationalError:
            # make migrations and migrate will fail with this (the class is loaded on startup)
            pass
        return service_choices

    services = forms.MultipleChoiceField(
        help_text=_("Choose if you want 24/7 access"),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label=_("Services"),
        choices=build_service_choices(),
    )


class FileImportForm(forms.Form):
    filetype = forms.ChoiceField(
        label="File type",
        choices=[("TITO", "Transactions (Nordea TITO)"), ("M", "Members (csv)")],
    )
    file = forms.FileField()


class CustomInvoiceForm(forms.Form):
    service = forms.ModelChoiceField(
        label=_("Service"),
        queryset=ServiceSubscription.objects.none(),
        empty_label=_("Choose service.."),
    )
    count = forms.IntegerField(
        label=_("How many units of service you want"), min_value=1, max_value=666
    )
