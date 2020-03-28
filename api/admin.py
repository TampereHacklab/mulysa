from django.contrib import admin

from .models import AccessDevice, DeviceAccessLogEntry


class AccessDeviceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "deviceid",
    ]


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
