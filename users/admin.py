from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import (
    BankTransaction,
    CustomUser,
    MemberService,
    MembershipApplication,
    ServiceSubscription,
    CustomInvoice,
    UsersLog,
    NFCCard,
)


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    ordering = (
        "first_name",
        "last_name",
    )
    list_display = (
        "email",
        "first_name",
        "last_name",
        "birthday",
        "language",
        "municipality",
        "phone",
        "mxid",
        "is_active",
    )
    list_filter = list_display
    fieldsets = (("Extra", {"fields": list_display}),)


class NFCCardAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "subscription",
        "cardid",
    ]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MembershipApplication)
admin.site.register(MemberService)
admin.site.register(ServiceSubscription)
admin.site.register(BankTransaction)
admin.site.register(CustomInvoice)
admin.site.register(UsersLog)
admin.site.register(NFCCard, NFCCardAdmin)
