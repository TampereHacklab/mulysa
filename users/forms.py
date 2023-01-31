from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from users.models.custom_user import CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone", "mxid", "language")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ("email", "first_name", "last_name", "phone", "mxid", "language")
