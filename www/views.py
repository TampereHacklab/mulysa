from django.shortcuts import render

from www.forms import RegistrationApplicationForm, RegistrationUserForm, MemberImportForm

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
    import_message = "Select file to import"
    if request.method == 'POST':
        form = MemberImportForm(request.POST, request.FILES)
        if form.is_valid():
            dataimport = DataImport()
            dataimport.importmembers(request.FILES['file'])
            import_message = "Imported data"
    else:
        form = MemberImportForm()
    return render(request, 'www/import.html', {'form': form, 'import_message': import_message })
