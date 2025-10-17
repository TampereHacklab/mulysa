from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.db.models import Count

from rangefilter.filters import DateRangeFilter

from .filters import (
    PredefAgeListFilter,
    MarkedForDeletionFilter,
    ServiceSubscriptionCountFilter,
)
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
    Statistics,
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
        "marked_for_deletion_on",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    search_fields = ("email", "first_name", "last_name", "phone", "mxid", "nick")
    list_filter = (
        "is_active",
        "is_staff",
        MarkedForDeletionFilter,
        "language",
        "municipality",
        PredefAgeListFilter,
        ("birthday", DateRangeFilter),
        ServiceSubscriptionCountFilter,
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

    add_fieldsets = (
        (
            "Data",
            {
                "classes": ("wide",),
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
                    "password1",
                    "password2",
                ),
            },
        ),
        (
            "Dates",
            {
                "classes": ("wide",),
                "fields": ("birthday",),
            },
        ),
    )

    inlines = [ServiceSubscriptionInline]

    actions = ["mark_for_deletion_on", "mark_for_deletion_off"]

    def mark_for_deletion_on(self, request, queryset):
        queryset.update(marked_for_deletion_on=timezone.now())

    mark_for_deletion_on.short_description = "Mark selected users for deletion"

    def mark_for_deletion_off(self, request, queryset):
        queryset.update(marked_for_deletion_on=None)

    mark_for_deletion_off.short_description = (
        "Remove mark for deletion from selected users"
    )


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
    list_display = [
        "name",
        "cost",
        "pays_also_service",
        "required_service",
        "accounting_id",
    ]


class AmountDirectionFilter(admin.SimpleListFilter):
    title = "Transaction Type"
    parameter_name = "type"

    def lookups(self, request, model_admin):
        return [
            ("deposit", "Deposits"),
            ("withdrawal", "Withdrawals"),
            ("zero", "Zero amount"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == "deposit":
            return queryset.filter(amount__gt=0)
        if value == "withdrawal":
            return queryset.filter(amount__lt=0)
        if value == "zero":
            return queryset.filter(amount=0)
        return queryset


class DuplicateTransactionIdFilter(admin.SimpleListFilter):
    title = "Duplicate Archival reference"
    parameter_name = "duplicate_archival_reference"

    def lookups(self, request, model_admin):
        return [
            ("yes", "Has duplicates"),
        ]

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            duplicates = (
                queryset.values("archival_reference")
                .annotate(txn_count=Count("id"))
                .filter(txn_count__gt=1)
                .values_list("archival_reference", flat=True)
            )
            return queryset.filter(archival_reference__in=list(duplicates))
        return queryset


class BankTransactionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "amount",
        "reference_number",
        "archival_reference",
        "date",
        "sender",
        "has_been_used",
    ]
    list_filter = (
        AmountDirectionFilter,
        "has_been_used",
        "date",
        DuplicateTransactionIdFilter,
    )
    ordering = ("-date",)
    search_fields = (
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__phone",
        "user__mxid",
        "user__nick",
        "reference_number",
        "archival_reference",
    )


class CustomInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "subscription",
        "payment_transaction",
        "reference_number",
        "amount",
    ]


class StatisticsAdmin(admin.ModelAdmin):
    """
    Allow only viewing statistics in admin
    """

    list_display = [
        field.name for field in Statistics._meta.fields if field.name != "id"
    ]

    date_hierarchy = "date"
    list_display_links = None
    actions = None

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(MembershipApplication)
admin.site.register(MemberService, MemberServiceAdmin)
admin.site.register(ServiceSubscription, ServiceSubscriptionAdmin)
admin.site.register(BankTransaction, BankTransactionAdmin)
admin.site.register(CustomInvoice, CustomInvoiceAdmin)
admin.site.register(UsersLog)
admin.site.register(NFCCard, NFCCardAdmin)
admin.site.register(Statistics, StatisticsAdmin)
