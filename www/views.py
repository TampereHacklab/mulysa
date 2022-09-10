from datetime import timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
import markdown
from django.utils.safestring import mark_safe

from api.models import DeviceAccessLogEntry
from drfx import settings
from users.models import (
    BankTransaction,
    CustomInvoice,
    CustomUser,
    MemberService,
    MembershipApplication,
    NFCCard,
    ServiceSubscription,
    UsersLog,
)
from utils import referencenumber
from utils.businesslogic import BusinessLogic
from utils.dataexport import DataExport
from utils.dataimport import DataImport
from www.forms import (
    CreateUserForm,
    CustomInvoiceForm,
    EditUserForm,
    FileImportForm,
    RegistrationApplicationForm,
    RegistrationServicesFrom,
    RegistrationUserForm,
)
from .decorators import self_or_staff_member_required


def register(request):
    if request.method == "POST":
        userform = RegistrationUserForm(request.POST)
        applicationform = RegistrationApplicationForm(request.POST)
        servicesform = RegistrationServicesFrom(request.POST)

        if (
            userform.is_valid()
            and applicationform.is_valid()
            and servicesform.is_valid()
        ):

            # extra handling for services that pay for other services
            # TODO: this logic should probably live in business logic
            memberservices = MemberService.objects.all()
            subscribed_services = []

            print(servicesform.cleaned_data.get("services"))

            for service in memberservices:
                if str(service.id) in servicesform.cleaned_data.get("services", []):
                    subscribed_services.append(service)
                    if service.pays_also_service:
                        subscribed_services.append(service.pays_also_service)

            # Convert to set for unique items
            subscribed_services = set(subscribed_services)

            new_user = userform.save(commit=False)
            new_application = applicationform.save(commit=False)
            new_user.save()
            new_application.user = new_user

            for service in subscribed_services:
                BusinessLogic.create_servicesubscription(
                    new_user, service, ServiceSubscription.SUSPENDED
                )

            # save only after subscriptions are saved also so that the email
            # knows about them
            new_application.save()

            return render(request, "www/thanks.html", {}, content_type="text/html")
    else:
        userform = RegistrationUserForm()
        applicationform = RegistrationApplicationForm()
        servicesform = RegistrationServicesFrom()
    return render(
        request,
        "www/register.html",
        {
            "userform": userform,
            "applicationform": applicationform,
            "servicesform": servicesform,
        },
        content_type="text/html",
    )


@login_required
@staff_member_required
def dataimport(request):
    report = None
    if request.method == "POST":
        form = FileImportForm(request.POST, request.FILES)
        if form.is_valid():
            dataimport = DataImport()
            if request.POST["filetype"] == "M":
                report = dataimport.importmembers(request.FILES["file"])
            if request.POST["filetype"] == "TITO":
                report = dataimport.import_tito(request.FILES["file"])
            if request.POST["filetype"] == "HOLVI":
                report = dataimport.import_holvi(request.FILES["file"])
    else:
        form = FileImportForm()
    return render(request, "www/import.html", {"form": form, "report": report})


@login_required
@staff_member_required
def dataexport(request):
    if "data" in request.GET:
        if request.GET["data"] == "memberstsv":
            return HttpResponse(
                DataExport.exportmembers(), content_type="application/tsv"
            )

        if request.GET["data"] == "accountingcsv":
            return HttpResponse(
                DataExport.exportaccounting(), content_type="application/csv"
            )

    return render(request, "www/export.html")


@login_required
@staff_member_required
def users(request):
    users = CustomUser.objects.all()
    services = MemberService.objects.filter(hidden=False)

    for user in users:
        user.servicesubscriptions = ServiceSubscription.objects.filter(user=user)

    return render(request, "www/users.html", {"users": users, "services": services})


@login_required
@staff_member_required
def ledger(request):
    filter = request.GET.get("filter")
    transactions = []
    if not filter:
        transactions = BankTransaction.objects.all().order_by("-date")
    elif filter == "unknown":
        transactions = BankTransaction.objects.filter(user=None).order_by("-date")
    elif filter == "paid":
        transactions = BankTransaction.objects.filter(amount__lte=0).order_by("-date")
    elif filter == "unused":
        transactions = BankTransaction.objects.filter(has_been_used=False).order_by(
            "-date"
        )

    return render(request, "www/ledger.html", {"transactions": transactions})


@login_required
@staff_member_required
def custominvoices(request):
    filter = request.GET.get("filter")  # For future expansion
    custominvoices = []
    if not filter:
        custominvoices = CustomInvoice.objects.all().order_by("payment_transaction")

    return render(
        request, "www/custominvoices.html", {"custominvoices": custominvoices}
    )


@login_required
@staff_member_required
def application_operation(request, application_id, operation):
    application = get_object_or_404(MembershipApplication, id=application_id)
    name = str(application.user)
    if operation == "reject":
        BusinessLogic.reject_application(application)
        messages.success(
            request, _("Rejected member application from %(name)s") % {"name": name}
        )
    if operation == "accept":
        BusinessLogic.accept_application(application)
        messages.success(
            request, _("Accepted member application from %(name)s") % {"name": name}
        )

    return applications(request)


@login_required
@staff_member_required
def applications(request):
    applications = MembershipApplication.objects.all()
    for application in applications:
        application.servicesubscriptions = set(
            ServiceSubscription.objects.filter(user=application.user)
        )

    return render(request, "www/applications.html", {"applications": applications})


@login_required
@self_or_staff_member_required
def userdetails(request, id):
    userdetails = CustomUser.objects.get(id=id)
    userdetails.servicesubscriptions = ServiceSubscription.objects.filter(
        user=userdetails
    )
    userdetails.transactions = BankTransaction.objects.filter(
        user=userdetails
    ).order_by("-date")
    userdetails.userslog = UsersLog.objects.filter(user=userdetails).order_by("-date")
    userdetails.custominvoices = CustomInvoice.objects.filter(user=userdetails)
    userdetails.membership_application = MembershipApplication.objects.filter(
        user=userdetails
    ).first()
    latest_transaction = BankTransaction.objects.order_by("-date").first()
    return render(
        request,
        "www/user.html",
        {
            "userdetails": userdetails,
            "bank_iban": settings.ACCOUNT_IBAN,
            "last_transaction": latest_transaction.date if latest_transaction else "-",
        },
    )


@login_required
@self_or_staff_member_required
def usersettings(request, id):
    # the base form for users basic information
    customuser = get_object_or_404(CustomUser, id=id)
    usereditform = EditUserForm(request.POST or None, instance=customuser)
    if usereditform.is_valid():
        usereditform.save()
        messages.success(request, _("User details saved"))

    # services we can unsubscribe from
    # we are the user
    # service selfsubscribe is on
    # subscription state is active
    own_self_subscribe_services = customuser.servicesubscription_set.all()
    unsubscribable_services = own_self_subscribe_services.filter(
        service__self_subscribe=True
    )
    # services we can subsribe to
    # service that has self_subscribe
    # and we don't already have that service (TODO: actually you could have one service multiple times...)
    subscribable_services = MemberService.objects.filter(self_subscribe=True).exclude(
        id__in=own_self_subscribe_services.values_list("service__id")
    )

    # find unclaimed nfc cards from the last XX minutes
    unclaimed_nfccards = (
        DeviceAccessLogEntry.objects.filter(
            granted=False,
            nfccard=None,
            claimed_by=None,
            date__gte=timezone.now() - timedelta(minutes=5),
        )
        .exclude(payload__isnull=True)
        .order_by("-date")
    )

    return render(
        request,
        "www/usersettings.html",
        {
            "usereditform": usereditform,
            "userdetails": customuser,
            "subscribable_services": subscribable_services,
            "unsubscribable_services": unsubscribable_services,
            "unclaimed_nfccards": unclaimed_nfccards,
        },
    )


@login_required
@self_or_staff_member_required
def usersettings_subscribe_service(request, id):
    """
    Subscribe user to new service
    """
    customuser = get_object_or_404(CustomUser, id=id)

    if request.method == "POST":
        service = get_object_or_404(MemberService, id=request.POST["serviceid"])

        # double check that it is ok to subsribe this service
        if ServiceSubscription.objects.filter(
            user=request.user, service=service
        ).count():
            messages.error(request, _("You already have this service"))
            return HttpResponseRedirect(reverse("usersettings", args=(customuser.id,)))
        if not service.self_subscribe:
            messages.error(request, _("This service cannot be self subscribed to"))
            return HttpResponseRedirect(reverse("usersettings", args=(customuser.id,)))

        # and subscribe
        BusinessLogic.create_servicesubscription(
            customuser, service, ServiceSubscription.OVERDUE
        )
        customuser.log(f"Self subscribed to {service.name}")
        messages.success(request, _("Service subscribed. You may now pay for it."))

    return HttpResponseRedirect(reverse("usersettings", args=(customuser.id,)))


@login_required
@self_or_staff_member_required
def usersettings_unsubscribe_service(request, id):
    """
    Unsubscribe user from service
    """
    customuser = get_object_or_404(CustomUser, id=id)

    if request.method == "POST":
        subscription = get_object_or_404(
            ServiceSubscription, id=request.POST["subscriptionid"]
        )
        if subscription.state == ServiceSubscription.ACTIVE:
            customuser.log(f"Self unsubscribing from {subscription.service.name}")
            subscription.delete()
            messages.success(request, _("Service unsubscribed"))
        else:
            messages.error(
                request,
                _(
                    "Service is not active. You must pay for the service first. Contact staff if needed."
                ),
            )

    return HttpResponseRedirect(reverse("usersettings", args=(customuser.id,)))


@login_required
@self_or_staff_member_required
def usersettings_claim_nfc(request, id):
    """
    claim nfc card for user
    """
    customuser = get_object_or_404(CustomUser, id=id)

    if request.method == "POST":
        logentry = get_object_or_404(
            DeviceAccessLogEntry, id=request.POST["logentryid"]
        )

        # mark the entry claimed
        logentry.claimed_by = customuser
        logentry.save()

        # save as a new card
        newcard = NFCCard(cardid=logentry.payload, user=customuser)
        newcard.save()

        # customer log entry
        censoredid = newcard.censored_id()
        customuser.log(f"Registered new NFC card {censoredid}")

        messages.success(request, _("NFC Card successfully claimed"))

    return HttpResponseRedirect(reverse("usersettings", args=(customuser.id,)))


@login_required
@self_or_staff_member_required
def usersettings_delete_nfc(request, id):
    """
    delete nfc card
    """
    customuser = get_object_or_404(CustomUser, id=id)

    if request.method == "POST":
        card = get_object_or_404(NFCCard, id=request.POST["nfccardid"])

        card.delete()

        # customer log entry
        censoredid = card.censored_id()
        customuser.log(f"Deleted NFC card {censoredid}")

        messages.success(request, _("NFC Card successfully deleted"))

    return HttpResponseRedirect(reverse("usersettings", args=(customuser.id,)))


@login_required
def custominvoice(request):
    days = 0
    amount = 0
    servicename = ""
    paid_invoices = CustomInvoice.objects.filter(
        user=request.user, payment_transaction__isnull=False
    )
    unpaid_invoices = CustomInvoice.objects.filter(
        user=request.user, payment_transaction__isnull=True
    )

    if request.method == "POST":
        form = CustomInvoiceForm(request.POST)
        form.fields["service"].queryset = ServiceSubscription.objects.filter(
            user=request.user
        ).exclude(state=ServiceSubscription.SUSPENDED)

        if form.is_valid():
            count = form.cleaned_data["count"]
            subscription = form.cleaned_data["service"]
            cost = form.cleaned_data["price"]

            days = subscription.service.days_per_payment * count
            amount = cost * count
            servicename = subscription.service.name

            if "create" in request.POST:
                invoice = CustomInvoice(
                    user=request.user,
                    subscription=subscription,
                    amount=amount,
                    days=days,
                )
                invoice.save()
                invoice.reference_number = referencenumber.generate(
                    settings.CUSTOM_INVOICE_REFERENCE_BASE + invoice.id
                )
                invoice.save()
    else:
        form = CustomInvoiceForm()
        form.fields["service"].queryset = ServiceSubscription.objects.filter(
            user=request.user
        ).exclude(state=ServiceSubscription.SUSPENDED)
    return render(
        request,
        "www/custominvoice.html",
        {
            "form": form,
            "paid_invoices": paid_invoices,
            "unpaid_invoices": unpaid_invoices,
            "days": days,
            "amount": amount,
            "servicename": servicename,
            "settings": settings,
        },
    )


@login_required
def custominvoice_action(request, action, invoiceid):
    # Todo: action is always delete
    invoice = CustomInvoice.objects.get(user=request.user, id=invoiceid)
    if invoice:
        if invoice.payment_transaction:
            print("Woot, custom invoice already paid, so wont delete!")
        else:
            invoice.delete()

    return custominvoice(request)


@login_required
def banktransaction_view(request, banktransactionid):
    """
    Allow user to view a "receipt" of a bank transaction
    """
    if request.user.is_staff:
        banktransaction = BankTransaction.objects.get(id=banktransactionid)
    else:
        banktransaction = BankTransaction.objects.get(
            user=request.user, id=banktransactionid
        )
    return render(
        request,
        "www/banktransaction.html",
        {
            "banktransaction": banktransaction,
            "settings": settings,
        },
    )


@login_required
@staff_member_required
def updateuser(request):
    if request.method == "POST":
        user = get_object_or_404(CustomUser, id=request.POST["userid"])
        BusinessLogic.updateuser(user)
        messages.success(request, _(f"Updateuser ran for user {user}"))
    return HttpResponseRedirect(reverse("users"))


@login_required
@staff_member_required
def createuser(request):
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect(reverse("userdetails", args=(new_user.id,)))
    else:
        form = CreateUserForm()
    return render(request, "www/createuser.html", {"userform": form})


@login_required
def changelog_view(request):
    """
    Just render the CHANGELOG.md file for users.
    """
    with open("CHANGELOG.md", "r", encoding="utf-8") as input_file:
        text = input_file.read()
    changelog = mark_safe(markdown.markdown(text))

    return render(request, "www/changelog.html", {"changelog": changelog})
