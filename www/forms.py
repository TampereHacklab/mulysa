from datetime import datetime

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from users import models
from users.models import MemberService, ServiceSubscription
from django.db.utils import OperationalError
from django.core.exceptions import ValidationError


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
            for service in MemberService.objects.filter(hidden=False):
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
        choices=build_service_choices,
        error_messages={"required": _("You must select at least one service")},
    )


class FileImportForm(forms.Form):
    filetype = forms.ChoiceField(
        label="File type",
        choices=[
            ("HOLVI", "Holvi (xls)"),
            ("TITO", "Transactions (Nordea TITO)"),
        ],
    )
    file = forms.FileField()


class CustomInvoiceServiceChoiceField(forms.ModelChoiceField):
    """
    Get better selection text for services in custom invoices.
    """

    def label_from_instance(self, obj):
        return _("%(servicename)s, %(cost)s") % {
            "servicename": obj.service.name,
            "cost": obj.service.cost_string(),
        }


class CustomInvoiceForm(forms.Form):
    service = CustomInvoiceServiceChoiceField(
        label=_("Service"),
        queryset=ServiceSubscription.objects.none(),
        empty_label=_("Choose service.."),
    )
    count = forms.IntegerField(
        label=_("How many units of service you want"), min_value=1, max_value=666
    )
    price = forms.DecimalField(
        label=_("Price per unit"),
        help_text=_("See price from the service selected above"),
        min_value=0.01,
    )

    def clean(self):
        """
        Super clean
        And check that the price matches with the selected service
        """
        cleaned_data = super().clean()
        subscription = cleaned_data["service"]
        service = subscription.service
        price = cleaned_data["price"]
        if service.cost_max and price > service.cost_max:
            raise forms.ValidationError(
                _("Price cannot be above service max cost: %(max)s"),
                params={"max": service.cost_max},
            )
        if service.cost_min and price < service.cost_min:
            raise forms.ValidationError(
                _("Cost cannot be below service min cost: %(min)s"),
                params={"min": service.cost_min},
            )
        # too tired to minimize these if statements :D
        if (not service.cost_min and not service.cost_max) and price != service.cost:
            raise forms.ValidationError(
                _("Price must be the service cost: %(cost)s"),
                params={"cost": service.cost},
            )


class EditUserForm(forms.ModelForm):
    class Meta:
        model = models.CustomUser
        fields = [
            "first_name",
            "last_name",
            "municipality",
            "nick",
            "mxid",
            "phone",
        ]

class EditAccountForm(forms.ModelForm):
    """Form for changing account information, such as email or password."""
    new_password1 = forms.CharField(
        label=_("New password"),
        required=False,
        widget=forms.PasswordInput,
        help_text=_("Leave blank if you do not want to change your password.")
    )
    new_password2 = forms.CharField(
        label=_("Confirm new password"),
        required=False,
        widget=forms.PasswordInput,
    )

    class Meta:
        model = models.CustomUser
        fields = [
            "email",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Store original email so we can avoid actually changing it before confirmation
        self._original_email = getattr(self.instance, "email", None)
        self._requested_email = None

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email:
            return email
        email = email.strip()
        norm = email.lower()
        qs = models.CustomUser.objects.filter(email__iexact=norm).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(_("The email address is already in use."))
        self._requested_email = norm
        return norm

    def clean(self):
        cleaned_data = super().clean()
        pw1 = cleaned_data.get("new_password1")
        pw2 = cleaned_data.get("new_password2")
        if pw1 or pw2:
            if pw1 != pw2:
                self.add_error("new_password2", _("The passwords do not match."))
            else:
                try:
                    validate_password(pw1, self.instance)
                except ValidationError as e:
                    self.add_error("new_password1", e)

        # Restore the instance's email to avoid in-memory mutation
        if hasattr(self, "_original_email"):
            self.instance.email = self._original_email
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Restore original email
        if hasattr(self, "_original_email"):
            user.email = self._original_email

        pw = self.cleaned_data.get('new_password1')
        if pw:
            user.set_password(pw)
        if commit:
            user.save()
        return user

    def get_requested_email(self):
        return self._requested_email or self.cleaned_data.get("email")


class CreateUserForm(forms.ModelForm):
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
