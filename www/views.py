from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.shortcuts import redirect

from drfx import settings
from users.models import (
    BankTransaction,
    CustomInvoice,
    CustomUser,
    MemberService,
    MembershipApplication,
    ServiceSubscription,
    UsersLog,
)
from www.forms import CustomInvoiceForm, FileImportForm, RegistrationApplicationForm, RegistrationUserForm

from utils import referencenumber
from utils.businesslogic import BusinessLogic
from utils.dataimport import DataImport


def register(request):
    if request.method == 'POST':
        userform = RegistrationUserForm(request.POST)
        applicationform = RegistrationApplicationForm(request.POST)

        memberservices = MemberService.objects.all()
        subscribed_services = []
        for service in memberservices:
            if 'service-' + str(service.id) in request.POST:
                subscribed_services.append(service)
                if service.pays_also_service:
                    subscribed_services.append(service.pays_also_service)

        # Convert to set for unique items
        subscribed_services = set(subscribed_services)

        if userform.is_valid() and len(subscribed_services) == 0:
            messages.error(request, _('Please select at least one member service'))

        if userform.is_valid() and applicationform.is_valid():
            new_user = userform.save(commit=False)
            new_application = applicationform.save(commit=False)
            new_user.save()
            new_application.user = new_user

            for service in subscribed_services:
                subscription = ServiceSubscription(user=new_user,
                                                   service=service,
                                                   state=ServiceSubscription.SUSPENDED)
                subscription.save()

            # save only after subscriptions are saved also so that the email
            # knows about them
            new_application.save()

            return render(request, 'www/thanks.html', {}, content_type='text/html')
    else:
        userform = RegistrationUserForm()
        applicationform = RegistrationApplicationForm()
    return render(request,
                  'www/register.html',
                  {
                      'userform': userform,
                      'applicationform': applicationform,
                      'memberservices': MemberService.objects.all()
                  },
                  content_type='text/html'
                  )

@login_required
@staff_member_required
def dataimport(request):
    report = None
    if request.method == 'POST':
        form = FileImportForm(request.POST, request.FILES)
        if form.is_valid():
            dataimport = DataImport()
            if request.POST['filetype'] == 'M':
                report = dataimport.importmembers(request.FILES['file'])
            if request.POST['filetype'] == 'TITO':
                report = dataimport.import_tito(request.FILES['file'])
    else:
        form = FileImportForm()
    return render(request, 'www/import.html', {'form': form, 'report': report})

@login_required
@staff_member_required
def users(request):
    users = CustomUser.objects.all()
    services = MemberService.objects.all()

    for user in users:
        user.servicesubscriptions = ServiceSubscription.objects.filter(user=user)

    return render(request, 'www/users.html', {
        'users': users,
        'services': services
    })

@login_required
@staff_member_required
def ledger(request):
    filter = request.GET.get('filter')
    transactions = []
    if not filter:
        transactions = BankTransaction.objects.all().order_by('-date')
    elif filter == 'unknown':
        transactions = BankTransaction.objects.filter(user=None).order_by('-date')
    elif filter == 'paid':
        transactions = BankTransaction.objects.filter(amount__lte=0).order_by('-date')
    elif filter == 'unused':
        transactions = BankTransaction.objects.filter(has_been_used=False).order_by('-date')

    return render(request, 'www/ledger.html', {
        'transactions': transactions
    })

@login_required
@staff_member_required
def custominvoices(request):
    filter = request.GET.get('filter')  # For future expansion
    custominvoices = []
    if not filter:
        custominvoices = CustomInvoice.objects.all().order_by('payment_transaction')

    return render(request, 'www/custominvoices.html', {
        'custominvoices': custominvoices
    })

@login_required
@staff_member_required
def application_operation(request, application_id, operation):
    application = get_object_or_404(MembershipApplication, id=application_id)
    name = str(application.user)
    if operation == 'reject':
        BusinessLogic.reject_application(application)
        messages.success(request, _('Rejected member application from %(name)s') % {'name': name})
    if operation == 'accept':
        BusinessLogic.accept_application(application)
        messages.success(request, _('Accepted member application from %(name)s') % {'name': name})

    return applications(request)

@login_required
@staff_member_required
def applications(request):
    applications = MembershipApplication.objects.all()
    for application in applications:
        application.servicesubscriptions = set(ServiceSubscription.objects.filter(user=application.user))

    return render(request, 'www/applications.html', {'applications': applications})

@login_required
def userdetails(request, id):
    if not request.user.is_superuser and request.user.id != id:
        return redirect('/www/login/?next=%s' % request.path)
    userdetails = CustomUser.objects.get(id=id)
    userdetails.servicesubscriptions = ServiceSubscription.objects.filter(user=userdetails)
    userdetails.transactions = BankTransaction.objects.filter(user=userdetails).order_by('date')
    userdetails.userslog = UsersLog.objects.filter(user=userdetails).order_by('date')
    userdetails.custominvoices = CustomInvoice.objects.filter(user=userdetails)
    userdetails.membership_application = MembershipApplication.objects.filter(user=userdetails).first()
    return render(request, 'www/user.html', {'userdetails': userdetails, 'defaultservice': settings.DEFAULT_ACCOUNT_SERVICE, 'bank_iban': settings.ACCOUNT_IBAN})

@login_required
def custominvoice(request):
    days = 0
    amount = 0
    servicename = ''
    paid_invoices = CustomInvoice.objects.filter(user=request.user, payment_transaction__isnull=False)
    unpaid_invoices = CustomInvoice.objects.filter(user=request.user, payment_transaction__isnull=True)

    if request.method == 'POST':
        form = CustomInvoiceForm(request.POST)
        form.fields['service'].queryset = ServiceSubscription.objects.filter(user=request.user).exclude(state=ServiceSubscription.SUSPENDED)

        if form.is_valid():
            count = int(form.cleaned_data['count'])
            if count <= 0:
                raise Exception('Invalid count, should never happen!')

            service_subscription_id = int(request.POST['service'])
            subscription = ServiceSubscription.objects.get(id=service_subscription_id)
            days = subscription.service.days_per_payment * count
            amount = subscription.service.cost * count
            servicename = subscription.service.name

            if 'create' in request.POST:
                invoice = CustomInvoice(user=request.user, subscription=subscription, amount=amount, days=days)
                invoice.save()
                invoice.reference_number = referencenumber.generate(settings.CUSTOM_INVOICE_REFERENCE_BASE + invoice.id)
                invoice.save()
    else:
        form = CustomInvoiceForm()
        form.fields['service'].queryset = ServiceSubscription.objects.filter(user=request.user).exclude(state=ServiceSubscription.SUSPENDED)
    return render(
        request,
        'www/custominvoice.html',
        {
            'form': form,
            'paid_invoices': paid_invoices,
            'unpaid_invoices': unpaid_invoices,
            'days': days,
            'amount': amount,
            'servicename': servicename,
        },
    )

@login_required
def custominvoice_action(request, action, invoiceid):
    # Todo: action is always delete
    invoice = CustomInvoice.objects.get(user=request.user, id=invoiceid)
    if invoice:
        if invoice.payment_transaction:
            print('Woot, custom invoice already paid, so wont delete!')
        else:
            invoice.delete()

    return custominvoice(request)

@login_required
@staff_member_required
def updateuser(request, id):
    user = CustomUser.objects.get(id=id)
    BusinessLogic.updateuser(user)
    return userdetails(request, id)
