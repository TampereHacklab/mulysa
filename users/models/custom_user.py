import datetime
import logging

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.custom_user_manager import CustomUserManager
from users.models.service_subscription import ServiceSubscription
from users.models.users_log import UsersLog

from users.validators import validate_mxid, validate_phone

from drfx import settings as drfx_settings

logger = logging.getLogger(__name__)


class CustomUser(AbstractUser):
    class Meta:
        ordering = (
            "first_name",
            "last_name",
        )

    # django kinda expects username field to exists even if we don't use it
    username = models.CharField(
        max_length=30,
        unique=False,
        blank=True,
        null=True,
        verbose_name="username not used",
        help_text="django expects that we have this field... TODO: figure out if we can get rid of this completely",
    )

    email = models.EmailField(
        unique=True,
        blank=False,
        verbose_name=_("Email address"),
        help_text=_(
            "Your email address will be used for important notifications about your membership"
        ),
        max_length=255,
    )

    # django does not make these mandatory by default, lets make them mandatory
    first_name = models.CharField(
        max_length=30, blank=False, null=False, verbose_name=_("First name")
    )
    last_name = models.CharField(
        max_length=150, blank=False, null=False, verbose_name=_("Last name")
    )

    municipality = models.CharField(
        blank=False,
        verbose_name=_("Municipality / City"),
        max_length=255,
    )

    nick = models.CharField(
        null=True,
        blank=True,
        verbose_name=_("Nick"),
        help_text=_("Nickname you are known with on Internet"),
        max_length=255,
    )

    mxid = models.CharField(
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("Matrix ID"),
        help_text=_("Matrix ID (@user:example.org)"),
        max_length=255,
        validators=[validate_mxid],
    )

    birthday = models.DateField(
        blank=False,
        verbose_name=_("Birthday"),
    )

    phone = models.CharField(
        blank=False,
        null=True,
        unique=True,
        verbose_name=_("Mobile phone number"),
        help_text=_(
            "This number will also be the one that gets access to the"
            " hacklab premises. International format (+35840123567)."
        ),
        error_messages={
            "unique": _("This phone number is already registered to a member"),
        },
        max_length=255,
        validators=[validate_phone],
    )

    bank_account = models.CharField(
        null=True,
        blank=True,
        verbose_name=_("Bank account"),
        help_text=_("Bank account for paying invoices (IBAN format: FI123567890)"),
        max_length=255,
    )

    language = models.CharField(
        max_length=10,
        verbose_name=_("Language"),
        help_text=_("Language preferred by user"),
        choices=drfx_settings.LANGUAGES,
        default=drfx_settings.LANGUAGE_CODE,
    )

    # some datetime bits
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("User creation date"),
        help_text=_("Automatically set to now when user is create"),
    )

    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified datetime"),
        help_text=_("Last time this user was modified"),
    )

    # when the member wants to leave we will mark now to this field and then have a cleanup script
    # to remove the members information after XX days
    marked_for_deletion_on = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Marked for deletion"),
        help_text=_(
            "Filled if the user has marked themself as wanting to end their membership"
        ),
    )

    # we don't really want to get any nicknames, plain email will do better
    # as our username
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "phone"]

    objects = CustomUserManager()

    def get_short_name(self):
        return self.email

    def natural_key(self):
        return self.email

    def log(self, message):
        logevent = UsersLog.objects.create(user=self, message=message)
        logevent.save()
        logger.info("User {}'s log: {}".format(logevent.user, message))

    def __str__(self):
        return self.first_name + " " + self.last_name

    def has_door_access(self):
        """
        helper method for checking if the user has access to open door
        TODO: this should probably be checked by businesslogic
        """
        if not self.is_active:
            return False
        try:
            subscription = self.servicesubscription_set.get(
                service=drfx_settings.DEFAULT_ACCOUNT_SERVICE
            )
            if subscription.state == ServiceSubscription.ACTIVE:
                return True
        except Exception:
            pass
        return False

    def has_suspended_services(self):
        """
        Helper method for checking if user has suspended services
        """
        # special case, always return False if membership application is still open
        if self.membershipapplication_set.count() > 0:
            return False

        for subscription in self.servicesubscription_set.all():
            if subscription.state == ServiceSubscription.SUSPENDED:
                return True

        return False

    def age_years(self):
        today = datetime.datetime.today()
        return int((today.date() - self.birthday).days / 365.25)
