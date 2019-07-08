from django.contrib import admin

from .models import SMSLog


# TODO: maybe move to utils or somewhere
class ReadOnlyAdmin(admin.ModelAdmin):
    """
    Simple read only admin model
    """
    actions = None

    def has_view_permission(self, request, obj=None):
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class SMSLogReadOnlyAdmin(ReadOnlyAdmin):
    list_display = ['created', 'to_number', 'message', 'via']
    readonly_fields = []


admin.site.register(SMSLog, SMSLogReadOnlyAdmin)
