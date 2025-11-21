from datetime import datetime

from django import forms
from django.db.utils import OperationalError
from django.forms.widgets import RadioSelect
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from formtools.wizard.views import SessionWizardView
from utils.businesslogic import BusinessLogic
from users import models
from users.models import MemberService, ServiceSubscription


class ServiceRadioSelect(RadioSelect):
    """Widget that displays services with descriptions and pricing information."""
    template_name = "www/registration/service_select.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._service_cache = {}

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)

        # Radio button options with service details
        if value:
            try:
                if value not in self._service_cache:
                    self._service_cache[value] = MemberService.objects.get(pk=value)
                service = self._service_cache[value]

                option['service_name'] = service.name
                option['description'] = service.description
                option['cost_info'] = f"{service.cost_string()} / {service.period_string()}"

                if service.pays_also_service:
                    option['includes_service'] = service.pays_also_service.name
            except (MemberService.DoesNotExist, ValueError):
                pass

        return option


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
        widgets = {
            "message": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": _("Optional message to the board...")
            })
        }

class RegistrationServicesForm(forms.Form):
    @staticmethod
    def build_service_choices():
        service_choices = []
        try:
            for service in MemberService.objects.filter(hidden=False, registration_form_visible=True):
                service_choices.append((service.pk, service.name))
        except OperationalError:
            # Catch migrations/migrate startup errors when tables don't exist yet
            pass
        return service_choices

    services = forms.ChoiceField(
        widget=ServiceRadioSelect,
        required=True,
        label=_("Services"),
        choices=build_service_choices,
        error_messages={"required": _("You must select one service")},
    )

class PersonalInfoForm(RegistrationUserForm):
    class Meta(RegistrationUserForm.Meta):
        fields = [
            "first_name",
            "last_name",
            "nick",
            "municipality",
            "birthday",
        ]

class ContactDetailsForm(RegistrationUserForm):
    class Meta(RegistrationUserForm.Meta):
        fields = [
            "email",
            "phone",
            "mxid",
            "language",
        ]

class ServiceSelectionForm(RegistrationServicesForm):
    pass

class AgreementForm(RegistrationApplicationForm):
    pass

class MembershipApplicationView(SessionWizardView):
    """Multi-step membership application form."""

    form_list = [
        ('personal', PersonalInfoForm),
        ('contact', ContactDetailsForm),
        ('services', ServiceSelectionForm),
        ('agreement', AgreementForm),
    ]

    templates = {
        'personal': 'www/registration/personal.html',
        'contact': 'www/registration/contact.html',
        'services': 'www/registration/services.html',
        'agreement': 'www/registration/agreement.html',
    }

    def get_template_names(self):
        return [self.templates[self.steps.current]]

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        # Build summary of all previous steps for the final agreement page
        if self.steps.current == 'agreement':
            personal = self.get_cleaned_data_for_step('personal') or {}
            contact = self.get_cleaned_data_for_step('contact') or {}
            services_data = self.get_cleaned_data_for_step('services') or {}

            service_id = services_data.get('services')
            services = []
            if service_id:
                try:
                    service = MemberService.objects.get(pk=service_id)
                    services.append(service)
                    if service.pays_also_service:
                        services.append(service.pays_also_service)
                except MemberService.DoesNotExist:
                    pass

            context.update({
                'summary_personal': personal,
                'summary_contact': contact,
                'summary_services': services,
            })
        return context

    def done(self, form_list, **kwargs):
        personal_form = form_list[0]
        contact_form = form_list[1]
        services_form = form_list[2]
        application_form = form_list[3]

        combined_user_data = {}
        combined_user_data.update(personal_form.cleaned_data)
        combined_user_data.update(contact_form.cleaned_data)

        application_data = application_form.cleaned_data.copy()

        userform = RegistrationUserForm(combined_user_data)
        applicationform = RegistrationApplicationForm(application_data)

        selected_id = services_form.cleaned_data.get("services")
        subscribed_services = set()

        # Include bundled services
        if selected_id:
            try:
                service = MemberService.objects.select_related("pays_also_service").get(pk=selected_id)
                subscribed_services.add(service)
                if service.pays_also_service:
                    subscribed_services.add(service.pays_also_service)
            except MemberService.DoesNotExist:
                pass

        # Create user and application objects
        new_user = userform.save(commit=False)
        new_application = applicationform.save(commit=False)
        new_user.save()
        new_application.user = new_user

        for service in subscribed_services:
            BusinessLogic.create_servicesubscription(
                new_user, service, ServiceSubscription.SUSPENDED
            )

        new_application.save()

        return redirect('membership_application_success')
