from django import forms
from django.utils.translation import gettext as _

from bootstrap_datepicker_plus import DatePickerInput
from users import models
from users.models import ServiceSubscription


class RegistrationUserForm(forms.ModelForm):
    class Meta:
        model = models.CustomUser
        fields = ['first_name', 'last_name', 'email', 'language', 'municipality',
                  'nick', 'mxid', 'birthday', 'phone']
        widgets = {
            'birthday': DatePickerInput(format='%d.%m.%Y')
        }

class RegistrationApplicationForm(forms.ModelForm):
    class Meta:
        model = models.MembershipApplication
        fields = ['message', 'agreement']

class FileImportForm(forms.Form):
    filetype = forms.ChoiceField(label='File type',
                                 choices=[
                                     ('TITO', 'Transactions (Nordea TITO)'), ('M', 'Members (csv)')
                                 ])
    file = forms.FileField()

class CustomInvoiceForm(forms.Form):
    service = forms.ModelChoiceField(label=_(u'Service'), queryset=ServiceSubscription.objects.none(), empty_label=_(u'Choose service..'))
    count = forms.IntegerField(label=_(u'How many units of service you want'), min_value=1, max_value=666)
