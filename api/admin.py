from django.contrib import admin

from .models import AccessDevice


class AccessDeviceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "deviceid",
    ]


admin.site.register(AccessDevice, AccessDeviceAdmin)
