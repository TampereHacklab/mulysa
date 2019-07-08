from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import CustomUser, MembershipApplication, MemberService, ServiceSubscription


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'birthday',
                    'municipality', 'phone', 'membership_plan', 'is_active']


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MembershipApplication)
admin.site.register(MemberService)
admin.site.register(ServiceSubscription)
