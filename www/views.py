from django.shortcuts import render

from users.models import CustomUser, MembershipApplication
from www.forms import FileImportForm, RegistrationApplicationForm, RegistrationUserForm

from utils.dataimport import DataImport


def register(request):
    if request.method == 'POST':
        userform = RegistrationUserForm(request.POST)
        applicationform = RegistrationApplicationForm(request.POST)
        print('POST', userform.is_valid(), applicationform.is_valid(), userform.errors)
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
    import_message = 'Select file to import'
    if request.method == 'POST':
        form = FileImportForm(request.POST, request.FILES)
        if form.is_valid():
            dataimport = DataImport()
            if request.POST['filetype'] == 'M':
                report = dataimport.importmembers(request.FILES['file'])
            if request.POST['filetype'] == 'T':
                report = dataimport.importnordea(request.FILES['file'])
            import_message = 'Import result: ' + str(report)
    else:
        form = FileImportForm()
    return render(request, 'www/import.html', {'form': form, 'import_message': import_message})

def users(request):
    return render(request, 'www/users.html', {'users': CustomUser.objects.all()})

def applications(request):
    return render(request, 'www/applications.html', {'applications': MembershipApplication.objects.all()})