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
                      'applicationform': applicationform
                  },
                  content_type='text/html'
                  )

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

def users(request):
    users = CustomUser.objects.all()
    services = MemberService.objects.all()

    for user in users:
        user.servicesubscriptions = ServiceSubscription.objects.filter(user=user)

    return render(request, 'www/users.html', {
        'users': users,
        'services': services
    })


def ledger(request):
    filter = request.GET.get('filter')
    transactions = []
    if not filter:
        transactions = BankTransaction.objects.all().order_by('-date')
    elif filter=='unknown':
        transactions = BankTransaction.objects.filter(user=None).order_by('-date')
    elif filter=='paid':
        transactions = BankTransaction.objects.filter(amount__lte=0).order_by('-date')

    return render(request, 'www/ledger.html', {
        'transactions': transactions
    })

def applications(request):
    return render(request, 'www/applications.html', {'applications': MembershipApplication.objects.all()})

def userdetails(request, id):
    user = CustomUser.objects.get(id=id)
    user.servicesubscriptions = ServiceSubscription.objects.filter(user=user)
    transactions = BankTransaction.objects.filter(user=user).order_by('-date')
    userslog = UsersLog.objects.filter(user=user).order_by('-date')
    return render(request, 'www/user.html', {'user': user, 'transactions': transactions, 'userslog': userslog})

def updateuser(request, id):
    user = CustomUser.objects.get(id=id)
    BusinessLogic.updateuser(user)
    return userdetails(request, id)
