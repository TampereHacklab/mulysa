from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

from .models import Config, Requisition


class RequisitionInline(admin.TabularInline):
    model = Requisition
    readonly_fields = ["valid_until", "ready", "deprecated"]
    exclude = ["nonce", "link", "requisition_id"]
    extra = 1
    max_num = 0
    can_delete = True


class ConfigAdmin(admin.ModelAdmin):
    list_display = ["api_id", "country", "institution", "config_actions"]
    search_fields = ("api_id",)
    list_filter = ("country", "institution")
    inlines = [RequisitionInline]
    readonly_fields = ["config_actions"]

    def get_urls(self):
        """
        inject our new action urls
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:id>/do-new-requisition/",
                self.admin_site.admin_view(self.do_new_requisition),
                name="nordigenautomation-do-new-requisition",
            ),
            path(
                "<int:id>/complete-requisition/<int:requisition_id>/",
                self.admin_site.admin_view(self.complete_requisition),
                name="nordigenautomation-complete-requisition",
            ),
        ]
        return custom_urls + urls

    def config_actions(self, obj):
        if obj.id and obj.api_id and obj.api_key and obj.country and obj.institution:
            return format_html(
                '<a class="button" href="{url}" title="{title}">{text}</a>'.format(
                    url=reverse(
                        "admin:nordigenautomation-do-new-requisition", args=[obj.pk]
                    ),
                    text=_("Do requisition"),
                    title=_(
                        "Initialize requisition, first time will just create a new requisition and successive clicks will create a new requisition and deprecate all the old ones"
                    ),
                )
            )
        return format_html(_("complete settings to get actions"))

    def do_new_requisition(self, request, *args, **kwargs):
        """
        Start new requisition process

        1) create new requisition object
        2) save the information
        3) redirect user to complete the requisition
        4) user comes back to "complete-requisition"
        """
        config = get_object_or_404(Config, id=kwargs["id"])

        try:
            req = config.create_new_requisition()
            return HttpResponseRedirect(req.link)
        except Exception as e:
            messages.add_message(
                request, messages.WARNING, f"Initializing requisition failed: {e}"
            )
        return redirect(
            reverse(
                "admin:nordigenautomation_config_change",
                kwargs={"object_id": config.pk},
            )
        )

    @csrf_exempt
    def complete_requisition(self, request, *args, **kwargs):
        """
        Mark the requisition as complete and redirect back to the form
        """
        config = get_object_or_404(Config, id=kwargs["id"])
        requisition = get_object_or_404(Requisition, id=kwargs["requisition_id"])

        if not requisition.config == config:
            return HttpResponseNotFound()

        if not request.GET.get("ref") == requisition.nonce:
            return HttpResponseNotFound()

        requisition.mark_completed()

        messages.add_message(request, messages.INFO, "Requisition has been completed")
        return redirect(
            reverse(
                "admin:nordigenautomation_config_change",
                kwargs={"object_id": config.pk},
            )
        )


admin.site.register(Config, ConfigAdmin)
