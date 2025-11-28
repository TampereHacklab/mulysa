import logging
from django.utils import timezone
from drfx import config
from django.db import models
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.utils import translation
from autoslug import AutoSlugField
from mailer import send_mail
from django.contrib.sites.models import Site

from users.models.custom_user import CustomUser

logger = logging.getLogger(__name__)

"""
Hardcoded categories that should always exist.
After changing these, run ./manage.py sync_email_categories to re-sync the DB (or create a migration).
"""
CATEGORY_TRANSACTIONAL = 'transactional'
CATEGORY_ANNOUNCEMENTS = 'system_announcements'

STATIC_CATEGORIES = {
    CATEGORY_TRANSACTIONAL: {
        'name': CATEGORY_TRANSACTIONAL,
        'display_name': "Transactional Emails",
        'display_name_en': "Transactional Emails",
        'display_name_fi': 'Toiminnalliset sähköpostit',
        'description': "Essential emails about your account and membership. These cannot be disabled.",
        'description_en': "Essential emails about your account and membership. These cannot be disabled.",
        'description_fi': "Tärkeitä viestejä tilistäsi ja jäsenyydestäsi. Näitä ei voi kytkeä pois päältä.",
        'user_configurable': False,
        'default_enabled': True,
        'sort_priority': 100
    },
    CATEGORY_ANNOUNCEMENTS: {
        'name': CATEGORY_ANNOUNCEMENTS,
        'display_name': "Announcements",
        'display_name_en': "Announcements",
        'display_name_fi': "Tiedotteet",
        'description': "Important announcements about the member system and the association.",
        'description_en': "Important announcements about the member system and the association.",
        'description_fi': "Kertaluontoisia tiedotteita järjestelmän ja yhdistyksen toiminnasta.",
        'user_configurable': True,
        'default_enabled': True,
        'sort_priority': 90
    }
}


class EmailCategory(models.Model):
    """
    Categories of email sent by the system
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name=_("Category Name"),
        help_text=_("Internal name for this category (e.g. 'newsletter', 'announcements').")
    )

    display_name = models.CharField(
        max_length=200,
        verbose_name=_("Display Name"),
        help_text=_("User-friendly display name for the category shown in email preferences.")
    )

    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("User-friendly explanation of what emails users will receive from this category.")
    )

    user_configurable = models.BooleanField(
        default=True,
        verbose_name=_("User Configurable"),
        help_text=_("If unchecked, users cannot opt out (e.g. for critical announcements.)")
    )

    default_enabled = models.BooleanField(
        default=True,
        verbose_name=_("Enabled by Default"),
        help_text=_("Whether users are subscribed to this category by default.")
    )

    sort_priority = models.IntegerField(
        default=0,
        verbose_name=_("Sort Priority"),
        help_text=_(
            "Categories with higher priority will be sorted first in user-facing lists (ties broken alphabetically).")
    )

    is_static = models.BooleanField(
        default=False,
        verbose_name=_("Static Category"),
        help_text=_("System-defined category that cannot be deleted")
    )

    created = models.DateTimeField(auto_now_add=True)

    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Email Category")
        verbose_name_plural = _("Email Categories")
        ordering = ['-sort_priority', 'display_name']

    def save(self, *args, **kwargs):
        if self.name in STATIC_CATEGORIES:
            self.is_static = True
        super().save(*args, **kwargs)

    @classmethod
    def get_category(cls, category_name):
        """
        Get or create a category by name.
        Ensures static categories always exist.
        """
        if category_name in STATIC_CATEGORIES:
            category, created = cls.objects.get_or_create(
                name=category_name,
                defaults=STATIC_CATEGORIES[category_name]
            )
            return category
        return cls.objects.get(name=category_name)

    def __str__(self):
        return self.display_name


class EmailPreference(models.Model):
    """
    User email preference per category
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='email_preferences'

    )
    category = models.ForeignKey(
        EmailCategory,
        on_delete=models.CASCADE,
        related_name='preferences'
    )
    enabled = models.BooleanField(default=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'category')
        verbose_name = _("Email Preference")
        verbose_name_plural = _("Email Preferences")

    def __str__(self):
        status = _("enabled") if self.enabled else _("disabled")
        return f"{self.user.email} - {self.category.display_name}: {status}"


class Email(models.Model):
    """
    Email to be sent to users
    """

    subject = models.CharField(
        blank=False,
        null=False,
        verbose_name=_("Subject"),
        help_text=_(
            "Descriptive subject for the email. Finnish / English both should be written here"
        ),
        max_length=512,
    )

    slug = AutoSlugField(populate_from="subject", unique=True)

    content = models.TextField(
        blank=False,
        null=False,
        verbose_name=_("Content"),
        help_text=_(
            "Content of the email. All emails will start with default 'View this message in browser' and end with 'You are receiving this message because') texts"
        ),
    )

    # some datetime bits
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Creation date"),
    )

    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified datetime"),
    )

    sent = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Datetime the message was sent")
    )

    category = models.ForeignKey(
        EmailCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Category"),
        help_text=_("Email category for preference filtering. Leave empty to send to all users.")
    )

    recipients_count = models.IntegerField(
        default=0,
        verbose_name=_("Recipients count"),
        help_text=_("Number of recipients the email was sent to.")
    )

    def get_recipient_queryset(self, base_qs):
        """
        Filter queryset based on email preferences for this category.
        """
        if not self.category:
            return base_qs

        if not self.category.user_configurable:
            return base_qs

        # Filter out users who have opted out
        opted_out_users = EmailPreference.objects.filter(
            category=self.category,
            enabled=False
        ).values_list('user_id', flat=True)

        # Also filter out users who have no preference and default is disabled
        if not self.category.default_enabled:
            users_with_preference = EmailPreference.objects.filter(
                category=self.category
            ).values_list('user_id', flat=True)
            enabled_users = EmailPreference.objects.filter(
                category=self.category,
                enabled=True
            ).values_list('user_id', flat=True)
            return base_qs.filter(id__in=enabled_users)
        return base_qs.exclude(id__in=opted_out_users)

    def queue_to_recipients(self, qs):
        """
        Send this message to recipients defined in the queryset,
        filtered by email preferences.

        Updates self.recipients_count with the number of users that the email will be sent to
        (after email preferences filtering).
        """
        filtered_qs = self.get_recipient_queryset(qs)

        for user in filtered_qs:
            logger.info(
                "Queuing email {email.subject} to {user.email}".format(
                    user=user, email=self
                )
            )
            user_lang = getattr(user, "language", None) or None
            with translation.override(user_lang):
                site = Site.objects.get_current()
                category_name = None
                category_is_configurable = False
                if getattr(self, "category", None):
                    category_name = self.category.display_name
                    category_is_configurable = self.category.user_configurable
                context = {
                    "user": user,
                    "config": config,
                    "email": self,
                    "SITENAME": site.name,
                    "SITE_URL": site.domain,
                    "category_name": category_name,
                    "category_is_configurable": category_is_configurable,
                }
                subject = self.subject
                from_email = config.NOREPLY_FROM_ADDRESS
                to = user.email
                plaintext_content = render_to_string("mail/email.txt", context)
                send_mail(subject, plaintext_content, from_email, [to])

        # save sent date to object to prevent sending again
        self.sent = timezone.now()
        self.recipients_count = filtered_qs.count()
        self.save()

    def get_url(self):
        return f"{self.sent.strftime('%s')}/{self.slug}"

    def get_epoch(self):
        if self.sent:
            return self.sent.strftime("%s")
        return "000"

    def __str__(self):
        return self.subject
