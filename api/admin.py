from django.contrib import admin

from .models import AccessDevice, DeviceAccessLogEntry


class AccessDeviceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "deviceid",
        "device_type",
        "allowed_services_list",
    ]

    def allowed_services_list(self, obj):
        return ", ".join([s.name for s in obj.allowed_services.all()])

    allowed_services_list.short_description = "Allowed services"


class DeviceAccessLogEntryAdmin(admin.ModelAdmin):
    list_display = [
        "date",
        "granted",
        "payload",
        "device",
        "nfccard",
    ]


admin.site.register(AccessDevice, AccessDeviceAdmin)
admin.site.register(DeviceAccessLogEntry, DeviceAccessLogEntryAdmin)
