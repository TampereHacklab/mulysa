from django.contrib import admin
from .models import Email

from django.utils.html import format_html
from django.urls import reverse, path
from django.utils.translation import ugettext_lazy as _
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404

from .forms import EmailActionForm


class EmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "draft", "sent", "email_actions")
    list_filter = ("draft", "sent")
    readonly_fields = ("created", "last_modified", "sent", "email_actions")

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
        return format_html(
            '<a class="button" href="{url}">{text}</a>'.format(
                url=reverse("admin:email-send", args=[obj.pk]), text=_("Send now"),
            )
        )

    def send_email(self, request, *args, **kwargs):
        email = get_object_or_404(Email, id=kwargs['id'])

        if request.method != "POST":
            form = EmailActionForm()

        else:
            form = EmailActionForm(request.POST)
            if form.is_valid():
                try:
                    form.save(email, request.user)
                except errors.Error as e:
                    # If save() raised, the form will a have a non
                    # field error containing an informative message.
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

        return TemplateResponse(request, "admin/send-email.html", context,)


admin.site.register(Email, EmailAdmin)
