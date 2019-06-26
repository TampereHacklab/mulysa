from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import ugettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, first_name, last_name, phone, password):
        user = self.model(email=email, first_name=first_name,
                          last_name=last_name, phone=phone)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self.db)
        return user


class CustomUser(AbstractUser):
    # Current membership plans available
    MEMBER_ONLY = 'MO'
    ACCESS_RIGHTS = 'AR'
    MEMBERSHIP_PLAN_CHOICES = [
        (MEMBER_ONLY, 'Membership only'),
        (ACCESS_RIGHTS, 'Member with access rights'),
    ]

    # django kinda expects username field to exists even if we don't use it
    username = models.CharField(
        max_length=30,
        unique=False,
        blank=True,
        null=True,
        verbose_name='username not used',
        help_text='django expects that we have this field... TODO: figure out if we can get rid of this completely'
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        verbose_name=_('Email address'),
        help_text=_(
            'Your email address will be used for important notifications about your membership'),
        max_length=255,
    )

    municipality = models.CharField(
        blank=False,
        verbose_name=_('Municipality / City'),
        max_length=255,
    )

    nick = models.CharField(
        blank=False,
        verbose_name=_('Nick'),
        help_text=_('IRC / Matrix nick or callsign'),
        max_length=255,
    )

    membership_plan = models.CharField(
        blank=False,
        verbose_name=_('Membership plan'),
        help_text=_('Access right grants 24/7 access and costs more than regular membership'),
        max_length=2,
        choices=MEMBERSHIP_PLAN_CHOICES,
        default=ACCESS_RIGHTS
    )

    birthday = models.DateField(
        blank=False,
        verbose_name=_('Birthday'),
    )

    phone = models.CharField(
        blank=False,
        verbose_name=_('Mobile phone number'),
        help_text=_(
            'This number will also be the one that gets access to the hacklab premises'),
        max_length=255,
    )

    # some datetime bits
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='User creation date',
        help_text='Automatically set to now when user is create'
    )
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last modified datetime'),
        help_text=_('Last time this user was modified'),
    )
    # datetime of last payment, the payment information itself will be in its own table
    last_payment_on = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Last payment'),
        help_text=_(
            'Last datetime this user had a payment transaction happen. TODO: should probably be dynamic'),
    )

    # when the member wants to leave we will mark now to this field and then have a cleanup script
    # to remove the members information after XX days
    marked_for_deletion_on = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Marked for deletion'),
        help_text=_(
            'Filled if the user has marked themself as wanting to end their membership'),
    )

    # we don't really want to get any nicknames, plain email will do better
    # as our username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone']

    objects = CustomUserManager()

    def get_short_name(self):
        return self.email

    def natural_key(self):
        return self.email

    def __str__(self):
        return self.email
