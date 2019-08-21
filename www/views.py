from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import render

from users.models import (BankTransaction, CustomUser, MemberService, MembershipApplication, ServiceSubscription,
                          UsersLog)
from www.forms import FileImportForm, RegistrationApplicationForm, RegistrationUserForm

from utils.businesslogic import BusinessLogic
from utils.dataimport import DataImport


def register(request):
    if request.method == 'POST':
        userform = RegistrationUserForm(request.POST)
        applicationform = RegistrationApplicationForm(request.POST)

        memberservices = MemberService.objects.all()
        for service in memberservices:
            print('service', service)
            if 'service-' + str(service.id) in request.POST:
                print('service selected!')
                # @todo continue here, create servicesubscritpions etc

        if userform.is_valid() and applicationform.is_valid():
            new_user = userform.save(commit=False)
            new_application = applicationform.save(commit=False)
            new_user.save()
            new_application.user = new_user
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

@staff_member_required
def applications(request):
    return render(request, 'www/applications.html', {'applications': MembershipApplication.objects.all()})

@login_required
def userdetails(request, id):
    if not request.user.is_superuser and request.user.id != id:
        return HttpResponseForbidden('Please login as this user or admin to see this')
    userdetails = CustomUser.objects.get(id=id)
    userdetails.servicesubscriptions = ServiceSubscription.objects.filter(user=userdetails)
    userdetails.transactions = BankTransaction.objects.filter(user=userdetails).order_by('-date')
    userdetails.userslog = UsersLog.objects.filter(user=userdetails).order_by('-date')
    return render(request, 'www/user.html', {'userdetails': userdetails})

@staff_member_required
def updateuser(request, id):
    user = CustomUser.objects.get(id=id)
    BusinessLogic.updateuser(user)
    return userdetails(request, id)
