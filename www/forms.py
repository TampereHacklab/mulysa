from django import forms

from users import models


class RegistrationUserForm(forms.ModelForm):
    class Meta:
        model = models.CustomUser
        fields = ['email', 'municipality', 'nick', 'membership_plan', 'birthday', 'phone']
    birthday = forms.DateField(widget=forms.DateInput(format='%d.%m.%Y'), input_formats=('%d.%m.%Y',))

class RegistrationApplicationForm(forms.ModelForm):
    class Meta:
        model = models.MembershipApplication
        fields = ['message', 'agreement']
