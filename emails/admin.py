from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import EmailActionForm
from .models import Email


class EmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "sent", "email_actions")
    list_filter = ("sent",)
    readonly_fields = ("slug", "created", "last_modified", "sent", "email_actions")

    def get_urls(self):
        """
        inject our new action urls
        """
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:id>/send/",
                self.admin_site.admin_view(self.send_email),
                name="email-send",
            ),
        ]
        return custom_urls + urls

    def email_actions(self, obj):
        """
        Get extra actions in admin views
        """
        if obj.sent:
            return format_html(
                '<a class="button" target="_blank" href="{url}">{text}</a>'.format(
                    url=reverse("email", args=[obj.created.strftime("%s"), obj.slug]),
                    text=_("Show browser version"),
                )
            )
        if obj.id:
            return format_html(
                '<a class="button" href="{url}">{text}</a>'.format(
                    url=reverse("admin:email-send", args=[obj.pk]),
                    text=_("Send now"),
                )
            )

    def send_email(self, request, *args, **kwargs):
        """
        Send the email
        """
        email = get_object_or_404(Email, id=kwargs["id"])

        if request.method != "POST":
            form = EmailActionForm()

        else:
            form = EmailActionForm(request.POST)
            if form.is_valid():
                try:
                    form.save(email, request.user)
                except Exception as e:
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
                    self.message_user(
                        request, f"Sending email failed: {e}", level=messages.ERROR
                    )
                    pass
                else:
                    self.message_user(request, "Success")
                    url = reverse(
                        "admin:emails_email_change",
                        args=[email.pk],
                        current_app=self.admin_site.name,
                    )
                    return HttpResponseRedirect(url)

        context = self.admin_site.each_context(request)
        context["opts"] = self.model._meta
        context["form"] = form
        context["email"] = email
        context["title"] = _("Send email")

        return TemplateResponse(
            request,
            "admin/send-email.html",
            context,
        )


admin.site.register(Email, EmailAdmin)
