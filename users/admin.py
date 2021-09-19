from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from rangefilter.filters import DateRangeFilter

from .filters import PredefAgeListFilter
from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import (
    BankTransaction,
    CustomInvoice,
    CustomUser,
    MemberService,
    MembershipApplication,
    NFCCard,
    ServiceSubscription,
    UsersLog,
)


class ServiceSubscriptionInline(admin.TabularInline):
    model = ServiceSubscription
    exclude = ["paid_until", "last_payment", "reference_number", "reminder_sent"]
    readonly_fields = ("last_payment", "reference_number")


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
        "nick",
        "mxid",
        "language",
        "municipality",
        "age_years",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    search_fields = ("email", "first_name", "last_name", "phone", "mxid", "nick")
    list_filter = (
        "is_active",
        "is_staff",
        "language",
        "municipality",
        PredefAgeListFilter,
        ("birthday", DateRangeFilter),
    )
    readonly_fields = (
        "age_years",
        "created",
        "last_modified",
        "last_login",
        "date_joined",
    )
    fieldsets = (
        (
            "Data",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "nick",
                    "mxid",
                    "language",
                    "municipality",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "phone",
                    "bank_account",
                )
            },
        ),
        (
            "Dates",
            {"fields": ("birthday",) + readonly_fields + ("marked_for_deletion_on",)},
        ),
    )
    inlines = [ServiceSubscriptionInline]


class NFCCardAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "cardid",
    ]


class ServiceSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "service", "state", "reference_number"]
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__phone",
        "user__mxid",
        "user__nick",
    )
    list_filter = ("service", "state")


class MemberServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "cost", "pays_also_service", "accounting_id"]


class BankTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "amount",
        "reference_number",
        "date",
        "sender",
        "has_been_used",
    ]
    list_filter = ("has_been_used",)
    ordering = ("date",)
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__phone",
        "user__mxid",
        "user__nick",
        "reference_number",
    )


class CustomInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "subscription",
        "payment_transaction",
        "reference_number",
        "amount",
    ]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MembershipApplication)
admin.site.register(MemberService, MemberServiceAdmin)
admin.site.register(ServiceSubscription, ServiceSubscriptionAdmin)
admin.site.register(BankTransaction, BankTransactionAdmin)
admin.site.register(CustomInvoice, CustomInvoiceAdmin)
admin.site.register(UsersLog)
admin.site.register(NFCCard, NFCCardAdmin)
