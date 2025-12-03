from django.contrib import admin

from .models import StorageReservation, StoragePayment, StorageService, StorageUnit


class StorageServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "pending_payment_days", "created_at"]
    readonly_fields = ["created_at", "updated_at"]


class StorageUnitAdmin(admin.ModelAdmin):
    list_display = [
        "service",
        "name",
        "price_per_month",
        "max_rental_months",
        "is_disabled",
        "status_display",
        "get_current_renter_admin",
    ]

    readonly_fields = ["created_at", "updated_at"]

    def status_display(self, obj):
        return obj.status

    status_display.short_description = "Status"


class StorageReservationAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "unit",
        "status",
        "start_date",
        "end_date",
        "total_paid_months",
        "reference_number",
        "pending_until",
        "paid_at",
    ]

    readonly_fields = [
        "created_at",
    ]


class StoragePaymentAdmin(admin.ModelAdmin):
    list_display = [
        "reservation",
        "reference_number",
        "amount",
        "months",
        "paid_at",
        "created_at",
    ]

    readonly_fields = ["created_at", "paid_at"]


admin.site.register(StorageService, StorageServiceAdmin)
admin.site.register(StorageUnit, StorageUnitAdmin)
admin.site.register(StorageReservation, StorageReservationAdmin)
admin.site.register(StoragePayment, StoragePaymentAdmin)
