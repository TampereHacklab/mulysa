from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser, MembershipApplication


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'birthday', 'municipality', 'phone', 'is_active']


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MembershipApplication)
