from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _

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
from www.forms import (
    CreateUserForm,
    CustomInvoiceForm,
    FileImportForm,
    RegistrationApplicationForm,
    RegistrationServicesFrom,
    RegistrationUserForm,
)

from utils import referencenumber
from utils.businesslogic import BusinessLogic
from utils.dataexport import DataExport
from utils.dataimport import DataImport


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
def userdetails(request, id):
    if not request.user.is_superuser and request.user.id != id:
        return redirect("/www/login/?next=%s" % request.path)
    userdetails = CustomUser.objects.get(id=id)
    userdetails.servicesubscriptions = ServiceSubscription.objects.filter(
        user=userdetails
    )
    userdetails.transactions = BankTransaction.objects.filter(
        user=userdetails
    ).order_by("date")
    userdetails.userslog = UsersLog.objects.filter(user=userdetails).order_by("date")
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
def usersettings(request, id):
    if not request.user.is_superuser and request.user.id != id:
        return redirect("/www/login/?next=%s" % request.path)
    if request.method == "POST":
        mxid = request.POST["mxid"]

        # Check if mxid changed
        if mxid != request.user.mxid:
            # Check for dupes:
            users = CustomUser.objects.filter(mxid=mxid).exclude(id=request.user.id)
            if len(users) > 0:
                messages.error(request, _("Matrix ID already in use"))
            else:
                if ("@" in mxid and ":" in mxid) or (len(mxid) == 0):
                    if len(mxid) == 0:
                        mxid = None
                    request.user.mxid = mxid
                    request.user.save()
                    messages.success(request, _("Matrix ID changed successfully"))
                    request.user.log(_("Set Matrix ID to %(mxid)s") % {"mxid": mxid})
                else:
                    messages.error(request, _("Invalid Matrix ID"))
        nick = request.POST["nick"]

        if nick != request.user.nick:
            request.user.nick = nick
            request.user.save()
            messages.success(request, _("Nickname changed successfully"))

    own_services = ServiceSubscription.objects.filter(user=request.user)
    self_services = MemberService.objects.filter(self_subscribe=True)
    subscribable_services = []
    unsubscribable_services = []

    for service in self_services:
        found = False
        for ssub in own_services:
            if ssub.service == service:
                found = True
        if found:
            if ssub.state == ServiceSubscription.ACTIVE:
                unsubscribable_services.append(service)
        else:
            subscribable_services.append(service)

    userdetails = CustomUser.objects.get(id=id)
    userdetails.nfccard = NFCCard.objects.filter(user=userdetails).first()
    if not userdetails.nfccard:
        # This monster finds unclaimed NFC cards stamped in last 5 minutes.
        userdetails.nfclog = (
            DeviceAccessLogEntry.objects.filter(
                granted=False,
                nfccard=None,
                date__gte=datetime.now() - timedelta(minutes=5),
            )
            .exclude(payload__isnull=True)
            .order_by("-date")
        )
    return render(
        request,
        "www/usersettings.html",
        {
            "userdetails": userdetails,
            "subscribable_services": subscribable_services,
            "unsubscribable_services": unsubscribable_services,
        },
    )


@login_required
def subscribe_service(request, id, serviceid):
    service = MemberService.objects.get(id=serviceid)
    already_existing = ServiceSubscription.objects.filter(
        user=request.user, service=service
    )
    if len(already_existing):
        messages.error(request, _("You already have this service"))
    else:
        BusinessLogic.create_servicesubscription(
            request.user, service, ServiceSubscription.OVERDUE
        )
        messages.success(request, _("Service subscribed. You may now pay for it."))
    return usersettings(request, id)


@login_required
def unsubscribe_service(request, id, serviceid):
    service = MemberService.objects.get(id=serviceid)
    subscriptions = ServiceSubscription.objects.filter(
        user=request.user, service=service
    )
    if len(subscriptions):
        for sub in subscriptions:
            if sub.state == ServiceSubscription.ACTIVE:
                subscriptions.delete()
                messages.success(request, _("Service unsubscribed"))
            else:
                messages.error(
                    request,
                    _(
                        "Service is not active. You must pay for the service first. Contact staff if needed."
                    ),
                )
    else:
        messages.error(request, _("You are not subscribed to that service"))
    return usersettings(request, id)


@login_required
def claim_nfc(request, id, cardid):
    userdetails = CustomUser.objects.get(id=id)

    if cardid == "RELEASE":
        nfccard = NFCCard.objects.get(user=userdetails)
        nfccard.delete()
        messages.success(request, _("Released NFC card"))
        userdetails.log(_("Released NFC card"))
    else:
        nfccards = NFCCard.objects.filter(cardid=cardid)
        if len(nfccards) > 0:
            raise Exception("This card is already claimed, should never happen!")
        newcard = NFCCard(cardid=cardid, user=userdetails)
        messages.success(request, _("NFC Card successfully claimed"))
        userdetails.log(_("NFC Card successfully claimed"))
        newcard.save()
    return usersettings(request, id)


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
            subscription = form.cleaned_data['service']
            cost = form.cleaned_data['price']

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
    if(request.user.is_staff):
        banktransaction = BankTransaction.objects.get(id=banktransactionid)
    else:
        banktransaction = BankTransaction.objects.get(user=request.user, id=banktransactionid)
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
def updateuser(request, id):
    user = CustomUser.objects.get(id=id)

    # First, generate any missing ref numbers
    subscriptions = ServiceSubscription.objects.filter(user=user)
    for subscription in subscriptions:
        if not subscription.reference_number:
            subscription.reference_number = referencenumber.generate(
                settings.SERVICE_INVOICE_REFERENCE_BASE + subscription.id
            )
            subscription.save()

    BusinessLogic.updateuser(user)
    return userdetails(request, id)


@login_required
@staff_member_required
def createuser(request):
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return userdetails(request, new_user.id)
    else:
        form = CreateUserForm()
    return render(request, "www/createuser.html", {"userform": form})
