from django.contrib import admin

from .models import AccessDevice, DeviceAccessLogEntry, AccessPermission


class AccessDeviceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "deviceid",
        "device_type",
        "allowed_permissions_list",
    ]

    def allowed_permissions_list(self, obj):
        return ", ".join([p.name for p in obj.allowed_permissions.all()])

    allowed_permissions_list.short_description = "Allowed permissions"


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
admin.site.register(AccessPermission)
