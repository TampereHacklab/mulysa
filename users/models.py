import datetime
import logging

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from drfx import settings as drfx_settings

logger = logging.getLogger(__name__)

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
    if len(value) < 3 or value[0] != '+' or not value[1:].isnumeric():
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
                          birthday, municipality, nick):
        if not email:
            raise ValueError(_('User must have an email address'))

        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            reference_number=reference_number,
            birthday=birthday,
            municipality=municipality,
            nick=nick
        )

        user.save(using=self.db)
        return user

class CustomUser(AbstractUser):
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
        null=True,
        blank=True,
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

    bank_account = models.CharField(
        null=True,
        blank=True,
        verbose_name=_('Bank account'),
        help_text=_('Bank account for paying invoices (IBAN format: FI123567890)'),
        max_length=255
    )

    language = models.CharField(max_length=10,
                                verbose_name=_('Language'),
                                help_text=_('Language preferred by user'),
                                choices=drfx_settings.LANGUAGES,
                                default=drfx_settings.LANGUAGE_CODE)

    # some datetime bits
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('User creation date'),
        help_text=_('Automatically set to now when user is create')
    )

    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last modified datetime'),
        help_text=_('Last time this user was modified'),
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
    reference_number = models.BigIntegerField(
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

    def log(self, message):
        logevent = UsersLog.objects.create(user=self, message=message)
        logevent.save()
        logger.info("User {}'s log: {}".format(logevent.user, message))

    def __str__(self):
        return self.first_name + ' ' + self.last_name

    def has_door_access(self):
        """
        helper method for checking if the user has access to open door
        TODO: this should probably be checked by businesslogic
        """
        logger.info(self.servicesubscription_set.all())
        try:
            subscription = self.servicesubscription_set.get(service=drfx_settings.DEFAULT_ACCOUNT_SERVICE)
            if(subscription.state == ServiceSubscription.ACTIVE):
                return True
        except Exception as e:
            logger.error(f"Tried to load servicesubscription that does not exists {e}")
        return False


def validate_agreement(value):
    if not value:
        raise ValidationError(_('You must agree to the terms'))


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
        validators=[validate_agreement]
    )

    def __str__(self):
        return _('Membership application for %(name)s') % {'name': str(self.user)}


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
        verbose_name='Normal cost of the service',
        validators=[MinValueValidator(0)],
    )

    """
    Defines another service that this this service pays for. If this service is paid, the referenced
    service is also marked as paid for days_per_payment after the payment date.

    Can be used to make service chains so that if a more expensive
    service is paid, the user can automatically receive cheaper ones.
    """
    pays_also_service = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True)

    # cost is used if not set
    cost_min = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Minimum payment',
        validators=[MinValueValidator(0)],
    )

    # Can be left out if no maximum needed
    cost_max = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Maximum payment',
        validators=[MinValueValidator(0)],
    )

    days_per_payment = models.IntegerField(
        verbose_name='How many days of service member gets for a valid payment',
        validators=[MinValueValidator(0)],
    )

    days_bonus_for_first = models.IntegerField(
        default=0,
        verbose_name='How many extra days of service member gets when paying for first time',
        validators=[MinValueValidator(0)],
    )

    days_before_warning = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='How many days befor payment expiration a warning message shall be sent',
        validators=[MinValueValidator(0)],
    )

    def __str__(self):
        return _('Member service') + ' ' + str(self.name)

    # Returns the cost of the service in human-readable string
    def cost_string(self):
        cs = str(self.cost) + '€ '
        if self.cost_min and self.cost_max:
            cs = cs + '(' + str(self.cost_min) + '€ - ' + str(self.cost_max) + '€)'
        return cs

    # Returns the period (days per payment) for the service in human-readable string
    def period_string(self):
        if self.days_per_payment == 31:
            return _('month')
        if self.days_per_payment == 365:
            return _('year')
        return str(self.days_per_payment) + ' ' + _('days')


class BankTransaction(models.Model):
    """
    Represents a incoming money transaction on the club's account.

    Mapped to user instance if possible.
    """

    # User this transaction was made by, or null if unknown
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)

    # Unique archival reference number that all transactions have
    archival_reference = models.CharField(
        blank=False,
        null=False,
        unique=True,
        verbose_name=_('Archival reference'),
        max_length=18,
    )
    date = models.DateField(
        verbose_name=_('Date'),
        help_text=_('Date of the transaction'),
    )
    amount = models.DecimalField(
        verbose_name=_('Amount'),
        help_text=_('Amount of money transferred to account'),
        max_digits=6,
        decimal_places=2
    )
    message = models.CharField(
        verbose_name=_('Message'),
        help_text=_('Message attached to transaction by sender. Should not normally be used.'),
        max_length=512,
    )
    sender = models.CharField(
        blank=True,
        null=True,
        verbose_name=_('Sender'),
        help_text=_('Sender of the transaction, if known.'),
        max_length=512,
    )
    reference_number = models.BigIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Reference number of transaction'),
        help_text=_('Reference number is set by transaction sender and should normally always be used.'),
    )
    transaction_id = models.CharField(
        blank=True,
        null=True,
        verbose_name=_('Transaction id'),
        help_text=_('Bank transaction id'),
        max_length=512,
    )
    code = models.CharField(
        blank=True,
        null=True,
        verbose_name=_('Code'),
        help_text=_('Code'),
        max_length=512,
    )
    has_been_used = models.BooleanField(
        blank=False,
        null=False,
        default=False,
        help_text=_('True, if this transaction has already been used to pay for service.')
    )

    def __str__(self):
        return f'Bank transaction for {(self.user and self.user.email) or "unknown user"}' \
            + f' from {self.sender}' \
            + f' {self.amount}€, reference {self.reference_number}' \
            + f', message {self.message or "(none)"}' \
            + f' at {self.date or "(no date)"}'


class ServiceSubscription(models.Model):
    """
    Represents user subscribing to a paid service.
    """
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
        (ACTIVE, _('Active')),
        (OVERDUE, _('Payment overdue')),
        (SUSPENDED, _('Suspended')),
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

    # Points to the latest payment that caused paid_until to update
    last_payment = models.ForeignKey(
        BankTransaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    SERVICE_STATE_COLORS = {
        ACTIVE: 'green',
        OVERDUE: 'yellow',
        SUSPENDED: 'red',
    }

    # Convenince method to get color of the state for ui
    def statecolor(self):
        return self.SERVICE_STATE_COLORS[self.state]

    def __str__(self):
        return _('Service %(servicename)s for %(username)s') % {'servicename': self.service.name, 'username': str(self.user)}


"""
A text log message for user activities (status changes, payments, etc)
"""
class UsersLog(models.Model):
    # User this log message is associated with
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date of this log event'
    )
    message = models.CharField(
        blank=False,
        verbose_name=_('Message'),
        max_length=1024,
    )

class CustomInvoice(models.Model):
    """
    Single invoice that can be used to pay for N units of service
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    subscription = models.ForeignKey(ServiceSubscription, on_delete=models.CASCADE)
    days = models.IntegerField(
        blank=False,
        null=False,
        verbose_name=_('How many days of service this invoice pays'),
        help_text=_('For example value 14 with access right service pays two weeks of access.'),
    )
    reference_number = models.BigIntegerField(
        blank=True,
        null=True,
        unique=True,
        verbose_name=_('Reference number for paying invoice'),
        help_text=_('Reference number is set by transaction sender and must match this.'),
    )
    amount = models.DecimalField(
        verbose_name=_('Amount'),
        help_text=_('Minimum amount of money to satisfy this invoice.'),
        max_digits=6,
        decimal_places=2
    )
    # Points to the payment, if this invoice has been paid.
    payment_transaction = models.ForeignKey(
        BankTransaction,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    def __str__(self):
        return _('Custom invoice to pay %(days)s days of %(servicename)s for %(username)s - %(amount)s€, reference: %(reference)s') % {
            'days': self.days,
            'servicename': self.subscription.service.name,
            'username': str(self.user),
            'amount': self.amount,
            'reference': self.reference_number
        }
