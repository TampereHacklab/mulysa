from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from modeltranslation.admin import TranslationAdmin

from .forms import EmailActionForm
from .models import Email, EmailCategory, EmailPreference

@admin.register(EmailCategory)
class EmailCategoryAdmin(TranslationAdmin):
    list_display = (
        'display_name',
        'name',
        'is_static',
        'user_configurable',
        'default_enabled',
        'sort_priority',
        'subscriber_count',
        'created'
    )
    list_filter = ('is_static', 'user_configurable', 'default_enabled', 'created')
    search_fields = ('name', 'display_name', 'description')
    list_editable = ('sort_priority',)
    readonly_fields = ('created', 'updated', 'subscriber_stats', 'subscriber_count', 'is_static')

    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'description')
        }),
        (_('Settings'), {
            'fields': ('user_configurable', 'default_enabled', 'sort_priority')
        }),
        (_('System'), {
            'fields': ('is_static',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created', 'updated', 'subscriber_stats'),
            'classes': ('collapse',)
        })
    )

    def subscriber_count(self, obj):
        """Show how many users are subscribed to this category."""
        count = obj.preferences.filter(enabled=True).count()
        total = obj.preferences.count()
        return f"{count} / {total}"
    subscriber_count.short_description = _("Subscribers")

    def subscriber_stats(self, obj):
        """Detailed subscriber statistisc"""
        if not obj.pk:
            return "-"

        enabled = obj.preferences.filter(enabled=True).count()
        disabled = obj.preferences.filter(enabled=False).count()
        from users.models import CustomUser
        total_users = CustomUser.objects.filter(is_active=True).count()
        no_preference = total_users - (enabled + disabled)

        return format_html(
            "<strong>Enabled:</strong> {} | <strong>Disabled:</strong> {} | <strong>No preference set:</strong> {}",
            enabled, disabled, no_preference
        )
    subscriber_stats.short_description = _("Detailed Statistics")

    def get_readonly_fields(self, request, obj=None):
        """
        Make static categories' critical fields read only
        """
        readonly = list(super().get_readonly_fields(request, obj))

        if obj and obj.is_static:
            readonly.extend(['name', 'user_configurable'])
        return readonly

    def has_delete_permission(self, request, obj = None):
        """
        Prevent deletion of static categories
        """
        if obj and obj.is_static:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(EmailPreference)
class EmailPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'enabled', 'updated')
    list_filter = ('enabled', 'category', 'updated')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    raw_id_fields = ('user',)

    def has_add_permission(self, request):
        return False

# This is apparently the only way to add help text to method-defined fields /__\
class EmailAdminForm(ModelForm):
    class Meta:
        model = Email
        help_texts = {'recipient_preview': _("Estimated based on current user preferences and active users. Save the email to update this.")}
        exclude = ()

class EmailAdmin(admin.ModelAdmin):
    form = EmailAdminForm

    list_display = ("subject", "category", "sent", "recipients_count", "email_actions")
    list_filter = ("sent", "category")
    readonly_fields = ("slug", "created", "last_modified", "sent", "recipients_count", "email_actions", "recipient_preview")

    fieldsets = (
        (None, {
            'fields': ('subject', 'category', 'content')
        }),
        (_("Metadata"), {
            'fields': ('slug', 'created', 'last_modified', 'sent'),
        }),
        (_("Recipients"), {
            'fields': ('recipient_preview', ),
        })
    )

    def recipient_preview(self, obj):
        """Show how many users will receive this email based on category."""
        if not obj.pk or obj.sent:
            return "-"

        from users.models import CustomUser
        all_active_users = CustomUser.objects.filter(is_active=True)

        if not obj.category:
            return format_html(
                "<strong>All active users:</strong> {}",
                all_active_users.count()
            )

        if not obj.category.user_configurable:
            return format_html(
                "<strong>All active users:</strong> {} (Category is not user-configurable)",
                all_active_users.count()
            )

        #Count users who haven't opted out
        opted_out = EmailPreference.objects.filter(
            category=obj.category,
            enabled=False,
            user__is_active=True
        ).count()
        total = all_active_users.count()
        will_receive = total - opted_out

        return format_html(
            "<strong>Will receive:</strong> {} | <strong>Opted out:</strong> {} | <strong>Total active:</strong> {}",
            will_receive, opted_out, total
        )
    recipient_preview.short_description = _("Recipient preview")

    def get_fieldsets(self, request, obj = None):
        """
        Show recipient preview for unsent mails, actual recipients for sent mails
        """
        base = list(super().get_fieldsets(request, obj))

        for idx, (title, options) in enumerate(base):
            if title == _("Recipients") or title == "Recipients":
                if getattr(obj, 'sent', None):
                    fields = ('recipients_count',)
                else:
                    fields = ('recipient_preview',)
                new_options = dict(options)
                new_options['fields'] = fields
                base[idx] = (title, new_options)
                break
        return tuple(base)

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
                '<a class="button" target="_blank" href="{url}">{text}</a>',
                    url=reverse("email", args=[obj.created.strftime("%s"), obj.slug]),
                    text=_("Show browser version")
            )
        if obj.id:
            return format_html(
                '<a class="button" href="{url}">{text}</a>',
                    url=reverse("admin:email-send", args=[obj.pk]),
                    text=_("Send now")
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

        category_name = None
        category_is_configurable = False
        if getattr(email, "category", None):
            category_name = email.category.display_name
            category_is_configurable = email.category.user_configurable
        context["category_name"] = category_name
        context["category_is_configurable"] = category_is_configurable

        return TemplateResponse(
            request,
            "admin/send-email.html",
            context,
        )


admin.site.register(Email, EmailAdmin)
