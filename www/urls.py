from django.urls import include, path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='www/index.html')),
    path('', include('django.contrib.auth.urls')),
    path('index', TemplateView.as_view(template_name='www/index.html'), name='index'),
    path('register', views.register, name='register'),
    path('dataimport', views.dataimport, name='dataimport'),
    path('users', views.users, name='users'),
    path('ledger', views.ledger, name='ledger'),
    path('userdetails/<int:id>/', views.userdetails, name='userdetails'),
    path('custominvoice', views.custominvoice, name='custominvoice'),
    path('custominvoice/<str:action>/<int:invoiceid>/', views.custominvoice_action, name='custominvoice_action'),
    path('updateuser/<int:id>/', views.updateuser, name='updateuser'),
    path('applications', views.applications, name='applications'),
    path('applications/<int:application_id>/<str:operation>', views.application_operation, name='application_operation'),
    path('i18n/', include('django.conf.urls.i18n')),
]
