import datetime

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator


def validate_mxid(value):
    # Empty is ok
    if len(value) == 0:
        return

    if len(value) < 3 or value[0] != '@' or ':' not in value:
        raise ValidationError(
            _('%(value)s is not a valid Matrix id. It must be in format @user:example.org'),
            params={'value': value},
        )

def validate_phone(value):
    if len(value) < 3 or value[0] != '+':
        raise ValidationError(
            _('%(value)s is not a valid phone number. It must be in international format +35840123567'),
            params={'value': value},
        )

class CustomUserManager(BaseUserManager):
    def create_superuser(self, email, first_name, last_name, phone, password):
        user = self.model(email=email, first_name=first_name,
                          last_name=last_name, phone=phone)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True

        # fill in some dummy data as they are required.
        # when registration works this wont be needed (we just need a way
        # of elevating a user to staff status)
        user.birthday = datetime.datetime.now()

        user.save(using=self.db)
        return user

    def create_customuser(self, email, first_name, last_name, phone, reference_number,
                          birthday, municipality, nick, membership_plan):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            reference_number=reference_number,
            birthday=birthday,
            municipality=municipality,
            nick=nick,
            membership_plan=membership_plan
        )

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
        help_text=_('Nickname you are known with on Internet'),
        max_length=255,
    )

    mxid = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Matrix ID'),
        help_text=_('Matrix ID (@user:example.org)'),
        max_length=255,
        validators=[validate_mxid],
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
        help_text=_('Format: DD.MM.YYYY'),
    )

    phone = models.CharField(
        blank=False,
        verbose_name=_('Mobile phone number'),
        help_text=_('This number will also be the one that gets access to the'
                    ' hacklab premises. International format (+35840123567).'),
        max_length=255,
        validators=[validate_phone],
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

    # this will be autofilled in post_save
    reference_number = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_('Reference number of membership fee payments'),
        help_text=_('Remember to always use your unique reference number for membership fee payments'),
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


"""
Extra fields for applying membership
"""
class MembershipApplication(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(
        blank=True,
        verbose_name=_('Message'),
        help_text=_('Free-form message to hacklab board'),
        max_length=1024,
    )

    agreement = models.BooleanField(
        blank=False,
        verbose_name=_('I agree to the terms presented'),
    )

    def __str__(self):
        return 'Membership application for ' + str(self.user)

"""
Class that represents a service for members. For example:
 - Yearly membership
 - Access rights
"""
class MemberService(models.Model):
    name = models.CharField(
        verbose_name=_('Service name'),
        help_text=_('Name of the service'),
        max_length=512,
    )
    cost = models.IntegerField(
        name="Cost normal",
        verbose_name="Normal cost of the service",
        validators=[MinValueValidator(0)],
    )
    # cost is used if not set
    cost_min = models.IntegerField(
        blank=True,
        null=True,
        name="Cost minimum",
        verbose_name="Minimum payment",
        validators=[MinValueValidator(0)],
    )
    # Can be left out if no maximum needed
    cost_max = models.IntegerField(
        blank=True,
        null=True,
        name="Cost maximum",
        verbose_name="Maximum payment",
        validators=[MinValueValidator(0)],
    )
    days_per_payment = models.IntegerField(
        name="Days per payment",
        verbose_name="How many days of service member gets for a valid payment",
        validators=[MinValueValidator(0)],
    )
    days_bonus_for_first = models.IntegerField(
        default=0,
        name="Bonus days for first payment of this service",
        verbose_name="How many extra days of service member gets when paying for first time",
        validators=[MinValueValidator(0)],
    )
    days_before_warning = models.IntegerField(
        blank=True,
        null=True,
        name="Days before warning",
        verbose_name="How many days befor payment expiration a warning message shall be sent",
        validators=[MinValueValidator(0)],
    )
    def __str__(self):
        return 'Member service ' + str(self.name)

"""
Represents user subscribing to a paid service. 
"""
class ServiceSubscription(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    service = models.ForeignKey(MemberService, on_delete=models.CASCADE)

    #   Service states:
    # Service is active, paid_until > current_date
    ACTIVE = 'ACTIVE'
    # Service suspended, user must contact administration to continue.
    # This is used for example if a member wants to pause paying for
    # certain time due to travel or other reason.
    # Also the initial state before membership is approved.
    #
    # Note: service must be paid fully until moving to suspended state.
    SUSPENDED = 'SUSPENDED'
    # Payment overdue, user must pay to activate service
    OVERDUE = 'OVERDUE'

    SERVICE_STATES = [
        (ACTIVE, 'Active'),
        (OVERDUE, 'Payment overdue'),
        (SUSPENDED, 'Suspended'),
    ]

    state = models.CharField(
        blank=False,
        verbose_name=_('Service state'),
        help_text=_('State of this service'),
        max_length=16,
        choices=SERVICE_STATES,
        default=SUSPENDED,
    )
    # The important paid until date. If this is not set, service has not been used yet or
    # has been suspended.
    paid_until = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Paid until'),
        help_text=_('The service will stay active until this date'),
    )
    def __str__(self):
        return 'Service ' + self.service.name + ' for ' + self.user.first_name + ' '+ self.user.last_name
