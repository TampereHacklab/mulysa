from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import BankTransaction, CustomUser, MemberService, MembershipApplication, ServiceSubscription


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'birthday',
                    'municipality', 'phone', 'reference_number', 'is_active']


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MembershipApplication)
admin.site.register(MemberService)
admin.site.register(ServiceSubscription)
admin.site.register(BankTransaction)
