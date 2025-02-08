import logging
from datetime import date, timedelta

from django.db.models import QuerySet
from django.template.loader import render_to_string
from django.utils import timezone, translation
from django.utils.translation import gettext as _

from drfx import config
from mailer import send_mail
from users.models import (
    BankTransaction,
    CustomInvoice,
    CustomUser,
    MemberService,
    ServiceSubscription,
)
from users.signals import application_approved, application_denied

from utils import referencenumber
from utils.matrixoperations import MatrixOperations

logger = logging.getLogger(__name__)


class BusinessLogic:
    """
    Implements business logic for the membership services.

    Contains a set of static methods callable from outside and some
    mostly internal ones.
    """

    @staticmethod
    def find_expiring_service_subscriptions():
        """
        Find users service subscriptions about to expire

        returns a queryset of the subscriptions that are about to expire in timerange
        defined by the service
        """
        today = timezone.now()
        qs = ServiceSubscription.objects.none()

        # each service has different timeframe, check each one independently
        for service in MemberService.objects.filter(
            days_before_warning__isnull=False
        ).all():
            days = service.days_before_warning
            checkdate = today + timedelta(days=days)
            qs = qs | ServiceSubscription.objects.filter(
                service=service,
                state=ServiceSubscription.ACTIVE,
                paid_until=checkdate.date(),
            )

        return qs

    @staticmethod
    def notify_expiring_service_subscriptions(qs: QuerySet):
        """
        Send notification for service subscriptions
        """
        for ss in qs:
            subject = _("Your subscription %(service_name)s is about to expire") % {
                "service_name": ss.service.name
            }
            from_email = config.NOREPLY_FROM_ADDRESS
            to = ss.user.email
            context = {
                "user": ss.user,
                "config": config,
                "subscription": ss,
            }
            # note, this template will be found from users app
            plaintext_content = render_to_string(
                "mail/service_subscription_about_to_expire.txt", context
            )
            send_mail(subject, plaintext_content, from_email, [to])
            ss.user.log(f"Expiry email notification sent. Subject: {subject} To: {to}")

    @staticmethod
    def new_transaction(transaction):
        """
        Called when a new transaction has been added into database
        """
        logger.debug(f"New transaction {transaction}")

        # Figure out a user for this transaction, if possible
        transaction_user = None

        if transaction.reference_number and transaction.reference_number != "":
            # Search subscriptions for reference..
            subscriptions = ServiceSubscription.objects.filter(
                reference_number=transaction.reference_number
            )

            if len(subscriptions) > 1:
                logger.warn(
                    "Suspicious: more than one service subscription with same reference!"
                )

            for subscription in subscriptions:
                transaction_user = subscription.user
                transaction_comment = f"New transaction for {subscription}"

            # Search custom invoices for reference..
            if not transaction_user:
                custominvoices = CustomInvoice.objects.filter(
                    reference_number=transaction.reference_number
                )

                if len(custominvoices) > 1:
                    logger.warn(
                        "Suspicious: more than one custominvoice with same reference!"
                    )

                for custominvoice in custominvoices:
                    transaction_user = custominvoice.user
                    transaction_comment = f"New transaction for {custominvoice}"

            if transaction_user:
                transaction.user = transaction_user
                transaction.comment = transaction_comment + "\n"
                transaction.save()

        if transaction.user:
            translation.activate(transaction.user.language)
            transaction.user.log(
                _("Bank transaction of %(amount)s€ dated %(date)s")
                % {"amount": str(transaction.amount), "date": str(transaction.date)}
            )

    @staticmethod
    def update_all_users():
        """
        Can be called from anywhere. Updates user data for all users.
        """
        all_users = CustomUser.objects.all()
        for user in all_users:
            BusinessLogic.updateuser(user)

    @staticmethod
    def updateuser(user):
        """
        Updates the user's status based on the data in database. Can be called from outside.
        """
        # Check for custom invoices..
        logger.debug("Examining custom invoices")
        invoices = CustomInvoice.objects.filter(
            user=user,
        )
        for invoice in invoices:
            transactions = BankTransaction.objects.filter(
                reference_number=invoice.reference_number, has_been_used=False
            )
            if len(transactions) > 1:
                logger.warn(
                    "Suspicious: more than one transaction matching custominvoice reference!"
                )

            for transaction in transactions:
                BusinessLogic._check_transaction_pays_custominvoice(transaction)

        servicesubscriptions = ServiceSubscription.objects.filter(user=user)

        # Check subscriptions
        for subscription in servicesubscriptions:
            logger.debug(f"Examining subscription {subscription}")
            BusinessLogic._updatesubscription(user, subscription, servicesubscriptions)
            BusinessLogic._check_servicesubscription_state(subscription)

    @staticmethod
    def reject_application(application):
        """
        Rejects a membership application and deletes the user
        """
        logger.debug(f"Rejecting app {application}")
        # TODO: Send mail and any other notifications to user?
        # Should delete the application
        application_denied.send(sender=application.__class__, instance=application)
        application.user.delete()

    @staticmethod
    def accept_application(application):
        """
        Accepts a membership application
        """
        logger.debug(f"Accepting app {application}")
        # TODO: Send mail and any other notifications to user?
        application_approved.send(sender=application.__class__, instance=application)
        user = application.user
        user.log(_("Accepted as member"))
        # Move user's subscriptions to overdue state
        for subscription in ServiceSubscription.objects.filter(user=user):
            subscription.state = ServiceSubscription.OVERDUE
            subscription.save()
            BusinessLogic._servicesubscription_state_changed(
                subscription, ServiceSubscription.SUSPENDED, subscription.state
            )

        application.delete()

        BusinessLogic.updateuser(user)

        # If user has Matrix ID and Matrix room is configured, invite the user
        if len(config.MATRIX_ACCESS_TOKEN) > 0 and user.mxid is not None:
            mo = MatrixOperations(config.MATRIX_ACCESS_TOKEN, config.MATRIX_SERVER)
            mo.invite_user(user.mxid, config.MATRIX_ROOM_ID, _("Accepted as member"))

    @staticmethod
    def create_servicesubscription(user, service, state):
        """
        Creates a new service subscription for wanted user and service
        Sets it to wanted state and generates a reference number for it.
        """
        subscription = ServiceSubscription(user=user, service=service, state=state)
        subscription.save()
        subscription.reference_number = referencenumber.generate(
            config.SERVICE_INVOICE_REFERENCE_BASE + subscription.id
        )
        subscription.save()
        return subscription

    # PRIVATE methods below - don't call these from outside (unless you know what you're doing!)

    @staticmethod
    def _check_servicesubscription_state(subscription):
        """
        Checks if the servicesubscription state needs to be changed due to paid_until changed.
        """
        # We do nothing if subscription is suspended
        if subscription.state == ServiceSubscription.SUSPENDED:
            return

        oldstate = subscription.state

        # Check if the service has been overdue and can be activated
        if (
            subscription.state == ServiceSubscription.OVERDUE
            and subscription.paid_until
            and subscription.paid_until > date.today()
        ):
            subscription.state = ServiceSubscription.ACTIVE
            subscription.save()
            BusinessLogic._servicesubscription_state_changed(
                subscription, oldstate, subscription.state
            )

        # Check if the service becomes overdue
        if (
            subscription.state == ServiceSubscription.ACTIVE
            and subscription.paid_until
            and subscription.paid_until < date.today()
        ):
            logger.debug(f"{subscription} payment overdue so changing state to OVERDUE")
            subscription.state = ServiceSubscription.OVERDUE
            subscription.save()
            BusinessLogic._servicesubscription_state_changed(
                subscription, oldstate, subscription.state
            )
        if (
            subscription.state == ServiceSubscription.OVERDUE
            and subscription.service.days_until_suspending
            and subscription.days_overdue() > subscription.service.days_until_suspending
        ):
            logger.debug(
                f"{subscription} has been overdue for {subscription.days_overdue()} days - suspending"
            )
            subscription.state = ServiceSubscription.SUSPENDED
            subscription.save()
            BusinessLogic._servicesubscription_state_changed(
                subscription, oldstate, subscription.state
            )

    @staticmethod
    def _servicesubscription_state_changed(subscription, oldstate, newstate):
        """
        This is called when service state changes.
        Can be used to trigger notifications or anything.
        """
        translation.activate(subscription.user.language)
        subscription.user.log(
            _("Service %(servicename)s state changed from %(oldstate)s to %(newstate)s")
            % {
                "servicename": subscription.service.name,
                "oldstate": oldstate,
                "newstate": newstate,
            }
        )

    @staticmethod
    def _check_transaction_pays_custominvoice(transaction):
        """
        Checks if given transaction pays any custom invoice
        """
        invoices = CustomInvoice.objects.filter(
            reference_number=transaction.reference_number,
        )

        for invoice in invoices:
            invoice_cost_min = invoice.cost_min()
            if (
                invoice.payment_transaction
                and config.CUSTOM_INVOICE_ALLOW_MULTIPLE_PAYMENTS is False
            ):
                transaction.comment += "Custom invoice is already paid and multiple payment is not allowed\n"
                transaction.save()
                break
            if (
                config.CUSTOM_INVOICE_DYNAMIC_PRICING
                and transaction.amount >= invoice_cost_min
                or transaction.amount >= invoice.amount
            ):
                subscription = ServiceSubscription.objects.get(
                    user=invoice.user, id=invoice.subscription.id
                )
                transaction.user = subscription.user
                inlimit = BusinessLogic._service_maxdays_after_payment_inlimit(
                    subscription,
                    transaction,
                    subscription.service.days_per_payment,
                )
                if inlimit is True:
                    BusinessLogic._service_paid_by_transaction(
                        subscription, transaction, invoice.days
                    )
                else:
                    subscription.user.log(
                        f"Payment of {invoice} would extend {subscription.service} paid to date over maximum by {inlimit} days. Transaction is not used"
                    )
                    transaction.comment += f"Service {subscription.service} paid untill date would get over maximum limit by {inlimit} days. Transaction is not used\n"
                    transaction.save()
            else:
                transaction.comment += f"Insufficient amount for invoice {invoice}\n"
                transaction.save()
                logger.debug(
                    f"Transaction {transaction} insufficient for invoice {invoice}"
                )

    @staticmethod
    def _updatesubscription(user, subscription, servicesubscriptions):
        """
        Updates a single subscription status for given user (used by updateuser)
        """
        logger.debug(f"Updating {subscription} for {user}")
        translation.activate(user.language)

        # Suspended subscriptions need manual action so can be skipped
        if subscription.state == ServiceSubscription.SUSPENDED:
            logger.debug("Service is suspended - no action")
            return

        if not subscription.reference_number:
            logger.debug("Service has no reference number - no action")
            return

        # Figure out other services that pay for this service
        services_that_pay_this = MemberService.objects.filter(
            pays_also_service=subscription.service
        )
        for service in services_that_pay_this:
            if BusinessLogic._user_is_subscribed_to(servicesubscriptions, service):
                logger.debug(
                    f"Service is paid by {service} which user is subscribed so skipping this service."
                )
                return

        # Check generic transactions that could pay for this service
        transactions = BankTransaction.objects.filter(
            reference_number=subscription.reference_number, has_been_used=False
        ).order_by("date")

        for transaction in transactions:
            if BusinessLogic._transaction_pays_service(
                transaction, subscription.service
            ):
                logger.debug(
                    f"Transaction is new and enough for service {subscription.service}"
                )
                inlimit = BusinessLogic._service_maxdays_after_payment_inlimit(
                    subscription,
                    transaction,
                    subscription.service.days_per_payment,
                )
                if inlimit is True:
                    BusinessLogic._service_paid_by_transaction(
                        subscription, transaction, subscription.service.days_per_payment
                    )
                else:
                    subscription.user.log(
                        f"Payment would extend {subscription.service} paid to date over maximum by {inlimit} days. {transaction} is not used"
                    )
                    transaction.user = subscription.user
                    transaction.comment += f"Service {subscription.service} paid untill date would get over maximum limit by {inlimit} days. Transaction is not used\n"
                    transaction.save()
            else:
                transaction.user = subscription.user
                transaction.comment += (
                    f"Amount insufficient to pay service {subscription.service}\n"
                )
                transaction.save()
                logger.debug(f"Transaction does not pay service {subscription.service}")

    @staticmethod
    def _transaction_pays_service(transaction, service):
        """
        Checks if given transaction pays the service. Returns boolean.
        """
        if service.cost_min and transaction.amount < service.cost_min:
            logger.debug(
                f"{transaction} amount is insuficent to pay {service} with lowered price"
            )
            return False
        if not service.cost_min and transaction.amount < service.cost:
            logger.debug(
                f"{service} has no .cost_min defined and {transaction} amount is insuficent to pay nominal price"
            )
            return False
        logger.debug(f"{transaction} is new and enough for service {service}")
        return True

    @staticmethod
    def _service_maxdays_after_payment_inlimit(
        servicesubscription,
        transaction,
        add_days,
    ):
        """
        Checks if payment of service would reach and pass .paid_until maximum limit. Returs true if in limit and days of limit exeede
        """
        if servicesubscription.paid_until:
            paid_until = servicesubscription.paid_until
        else:
            paid_until = transaction.date
            logger.debug(
                "Service has never been paid, using transaction date as last payment date"
            )
        date_after_payment = paid_until + timedelta(days=add_days)
        if (
            servicesubscription.service.days_maximum
            and 0 < servicesubscription.service.days_maximum
        ):
            date_max = transaction.date + timedelta(
                days=servicesubscription.service.days_maximum
            )
            delta_date = date_after_payment - date_max
        else:
            logger.debug(
                f"Service.days_maximum of {servicesubscription.service} is not defined or is zero, unlimited days?"
            )
            return True
        if date_after_payment <= date_max:
            logger.debug(
                f"Date after payment is inlimit with {servicesubscription.service} service.days_maximum "
            )
            return True
        logger.debug(
            f"Payment would extend {servicesubscription.service} paid to date over maximum {servicesubscription.service.days_maximum} days by {delta_date.days} days."
        )
        return delta_date.days

    @staticmethod
    def _user_is_subscribed_to(servicesubscriptions, service):
        """
        Returns True if user (whose servicesubscriptions is given) is subscribed to given service
        """
        for subscription in servicesubscriptions:
            if subscription.service == service:
                return True
        return False

    @staticmethod
    def _service_paid_by_transaction(servicesubscription, transaction, add_days):
        """
        Called if transaction actually pays for extra time on given service subscription
        """
        translation.activate(servicesubscription.user.language)

        logger.debug(f"Paying {servicesubscription} and gained {add_days} days more")

        # How many days to add to subscription's paid until
        days_to_add = timedelta(days=add_days)
        # First payment - initialize with payment date and add first time bonus days
        if not servicesubscription.paid_until:
            bonus_days = timedelta(
                days=servicesubscription.service.days_bonus_for_first
            )
            logger.debug(
                f"{servicesubscription} paid for first time, adding bonus of {bonus_days}"
            )
            transaction.comment += f"First payment of {servicesubscription} - added {bonus_days.days} bonus days.\n"

            days_to_add = days_to_add + bonus_days
            servicesubscription.paid_until = transaction.date

        # TODO Check maximum time that can be paid and limit payments to it.

        # Add days and mark this transaction to be the last payment
        servicesubscription.paid_until = servicesubscription.paid_until + days_to_add
        servicesubscription.last_payment = transaction
        servicesubscription.save()

        # Mark transaction as used
        transaction.user = servicesubscription.user
        transaction.has_been_used = True
        transaction.comment += f"Successful payment of {servicesubscription}\n"
        transaction.save()

        servicesubscription.user.log(
            _("%(servicename)s is now paid until %(until)s due to %(transaction)s")
            % {
                "servicename": str(servicesubscription),
                "until": str(servicesubscription.paid_until),
                "transaction": str(transaction),
            }
        )

        # Handle case where this service also pays for another service
        if servicesubscription.service.pays_also_service:
            # All subscription for current user paid by this service
            paid_servicesubscriptions = ServiceSubscription.objects.filter(
                user=servicesubscription.user,
                service=servicesubscription.service.pays_also_service,
            )
            for paid_servicesubscription in paid_servicesubscriptions:
                logger.debug(
                    f"{servicesubscription} also pays for {paid_servicesubscription}"
                )
                if paid_servicesubscription.state == ServiceSubscription.SUSPENDED:
                    logger.debug("Service is suspended - no action")
                else:
                    added_days = servicesubscription.paid_until - transaction.date
                    child_days = 0
                    if paid_servicesubscription.paid_until:
                        if paid_servicesubscription.paid_until > transaction.date:
                            child_date = (
                                paid_servicesubscription.paid_until - transaction.date
                            )
                            child_days = child_date.days

                    extra_days = (
                        added_days.days
                        - servicesubscription.service.days_per_payment
                        + paid_servicesubscription.service.days_per_payment
                        - child_days
                    )

                    logger.debug(
                        f"""Child prosess add days calculted by
                              {added_days.days}
                            - {servicesubscription.service.days_per_payment}
                            + {paid_servicesubscription.service.days_per_payment}
                            - {child_days}
                            = gained {extra_days} days more"""
                    )
                    # Calculate child subscription payment to happen at same time that latest parrent subsciption,
                    # useful with custominvoices that pays Parent subscription multiple times
                    BusinessLogic._service_paid_by_transaction(
                        paid_servicesubscription, transaction, extra_days
                    )

                    BusinessLogic._check_servicesubscription_state(
                        paid_servicesubscription
                    )
