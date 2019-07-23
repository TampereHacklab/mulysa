from django import forms

from users import models


class RegistrationUserForm(forms.ModelForm):
    class Meta:
        model = models.CustomUser
        fields = ['first_name', 'last_name', 'email', 'municipality',
                  'nick', 'mxid', 'membership_plan', 'birthday', 'phone']
    birthday = forms.DateField(widget=forms.DateInput(format='%d.%m.%Y'), input_formats=('%d.%m.%Y',))

class RegistrationApplicationForm(forms.ModelForm):
    class Meta:
        model = models.MembershipApplication
        fields = ['message', 'agreement']

class FileImportForm(forms.Form):
    filetype = forms.ChoiceField(label='File type',
                                choices=[
                                    ('M', 'Members (csv)'), ('T', 'Transactions (Nordea csv)')
                                ])
    file = forms.FileField()
