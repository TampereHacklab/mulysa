from uuid import uuid4
from datetime import timedelta

from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.sites.models import Site

from nordigen import NordigenClient


class Config(models.Model):
    """
    Configuration for nordigen connection.

    You can have multiple nordigen configurations. Each configuration gets new
    requisition_id when connection to nordigen is made.

    requisitions expire after 90 days of making the connection so those
    need to be refreshed manually every once in a while.
    """

    # Extend this as needed, for now only Finland is supported
    NORDIGEN_COUNTRY_CHOICES = [
        ("FI", "FI"),
        ("XX", "XX"),
    ]

    # Extend this as needed, for now only few of the finnish instituions
    # are supported
    NORDIGEN_INSTITUTION_CHOICES = [
        ("Bank Norwegian", "Bank Norwegian"),
        ("Danske Bank Business", "Danske Bank Business"),
        ("Danske Bank Private", "Danske Bank Private"),
        ("Handelsbanken Corporate", "Handelsbanken Corporate"),
        ("Handelsbanken Private", "Handelsbanken Private"),
        ("N26 Bank", "N26 Bank"),
        ("Nordea Business", "Nordea Business"),
        ("Nordea Corporate", "Nordea Corporate"),
        ("Nordea Personal", "Nordea Personal"),
        ("Oma Säästöpankki", "Oma Säästöpankki"),
        ("OP Financial Group", "OP Financial Group"),
        ("PayPal", "PayPal"),
        ("POP Pankki", "POP Pankki"),
        ("Resurs Bank", "Resurs Bank"),
        ("Revolut", "Revolut"),
        ("S-Pankki", "S-Pankki"),
        ("SEB Kort Bank AB", "SEB Kort Bank AB"),
        ("SEB Kort Bank AB Corporate", "SEB Kort Bank AB Corporate"),
        ("Stripe", "Stripe"),
        ("Säästöpankki", "Säästöpankki"),
        ("Wise", "Wise"),
        ("Ålandsbanken", "Ålandsbanken"),
        ("Sandbox Finance", "Sandbox Finance"),
    ]

    api_id = models.CharField(
        blank=False,
        verbose_name=_("Nordigen API id"),
        max_length=1024,
    )
    api_key = models.CharField(
        blank=False,
        verbose_name=_("Nordigen API key"),
        max_length=1024,
    )
    country = models.CharField(
        blank=False,
        verbose_name=_("Nordigen API country"),
        max_length=2,
        choices=NORDIGEN_COUNTRY_CHOICES,
    )
    institution = models.CharField(
        blank=False,
        verbose_name=_("Nordigen API Institution"),
        max_length=256,
        choices=NORDIGEN_INSTITUTION_CHOICES,
    )

    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Creation date"),
        help_text=_("Automatically set to now"),
    )
    last_modified = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last modified datetime"),
        help_text=_("Automatically updated"),
    )

    def get_active_requisition(self):
        """
        One config has none or at most one active requisition
        """
        try:
            requisition = self.requisition_set.get(
                deprecated=False, ready=True, valid_until__gte=timezone.now()
            )
        except Requisition.DoesNotExist:
            requisition = None
        return requisition

    def _get_client(self) -> NordigenClient:
        """
        Get nordigen client
        """
        if not hasattr(self, "_client"):
            self._client = NordigenClient(
                secret_id=self.api_id, secret_key=self.api_key
            )
            self._token_data = self._client.generate_token()
            self._token = self._client.exchange_token(self._token_data["refresh"])

            self._institution_id = self._client.institution.get_institution_id_by_name(
                country=self.country, institution=self.institution
            )

        return self._client

    def create_new_requisition(self):
        """
        Create new requisition for this config

        Returns the new requisition object that has been filled with
        requisition_id and link for doing the authorization process
        for it
        """

        # build new requisition
        requisition = Requisition()
        requisition.nonce = str(uuid4())
        requisition.config = self
        requisition.ready = False
        requisition.save()

        # and start the requisition process to get the required values from
        # nordigen
        requisition.do_init()
        return requisition


class OnlyActiveRequisitionsManager(models.Manager):
    """
    Get only active and usable requisitions
    """

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(deprecated=False, ready=True, valid_until__gte=timezone.now())
        )


class Requisition(models.Model):
    """
    Requisition for nordigen

    When new requisition is completed it will deprecate all the old requisitions
    for this configuration
    """

    objects = models.Manager()
    active = OnlyActiveRequisitionsManager()

    config = models.ForeignKey(Config, on_delete=models.CASCADE)
    nonce = models.CharField(
        blank=True,
        verbose_name=_("Nonce for verification purposes"),
        max_length=1024,
    )
    link = models.CharField(
        blank=True,
        verbose_name=_("Nordigen URL to handle the requisition"),
        max_length=1024,
    )
    requisition_id = models.CharField(
        blank=True,
        verbose_name=_("Nordigen Requisition id"),
        max_length=1024,
    )
    valid_until = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("How long this requisition id is valid untill"),
    )
    ready = models.BooleanField(
        default=False,
        verbose_name=_(
            "Is the requisition valid (user has completed the operation required)"
        ),
    )
    deprecated = models.BooleanField(
        default=False,
        verbose_name=_("Deprecated requisition"),
    )

    def __str__(self):
        if self.ready:
            return "Current requisition"
        if not self.ready:
            return "Requisition waiting for completion"
        if self.deprecated:
            return "Deprecated requisition"
        return "Requisition"

    def _build_absolute_complete_url(self):
        """
        Build absolute url to complete this requisition

        nordigen will add our nonce as "ref" query parameter
        """
        domain = Site.objects.get_current().domain
        scheme = "https"
        if "localhost" in domain:
            scheme = "http"
        path = f"/admin/nordigenautomation/config/{self.config.pk}/complete-requisition/{self.pk}/"
        return f"{scheme}://{domain}{path}"

    def do_init(self):
        """
        Initialize requisition and get the redirect url
        """
        config = self.config
        client = config._get_client()

        # cannot use reverse here as url router does not know about our
        # complete-requisition-url
        complete_url = self._build_absolute_complete_url()

        init = client.initialize_session(
            institution_id=config._institution_id,
            # redirect url after successful authentication
            redirect_uri=complete_url,
            # additional layer of unique ID defined by you
            reference_id=self.nonce,
        )

        # save the data
        self.link = init.link
        self.requisition_id = init.requisition_id
        # tehcnically this is valid for 90 days but lets give
        # one day of room for timezone stuff :)
        self.valid_until = timezone.now() + timedelta(days=89)
        self.save()

        return self

    def mark_completed(self):
        # deprecate all the other requisitions for this config
        config = self.config
        Requisition.objects.filter(config=config, deprecated=False).exclude(
            id=self.id
        ).update(deprecated=True)

        # mark our as not deprecated and ready
        self.deprecated = False
        self.ready = True
        self.save()

    def get_transactions(self, date_from=None, date_to=None):
        """
        With valid and not deprecated requisition get transactions

        NOTE: this will get transactions for ALL accounts that the user
        selected for this requisition
        """
        if not self.ready:
            raise Exception("Requisition is not yet ready, run do_init first")
        if self.deprecated:
            raise Exception("Cannot get transactions with deprecated requisition")
        if not self.valid_until or self.valid_until < timezone.now():
            raise Exception("Requisition is not valid yet or anymore")

        # get all accounts
        accounts = self.config._get_client().requisition.get_requisition_by_id(
            requisition_id=self.requisition_id
        )

        # convert from to to strings for api
        if date_from:
            date_from = date_from.strftime("%Y-%m-%d")
        if date_to:
            date_to = date_to.strftime("%Y-%m-%d")

        data = []
        # get all transactions from accounts
        for account_id in accounts["accounts"]:
            account = self.config._get_client().account_api(id=account_id)
            transactions = account.get_transactions(
                date_from=date_from, date_to=date_to
            )
            return transactions

        return data
