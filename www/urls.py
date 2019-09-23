from django.urls import path, include
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='www/index.html')),
    path('index', TemplateView.as_view(template_name='www/index.html'), name='index'),
    path('register', views.register, name='register'),
    path('dataimport', views.dataimport, name='dataimport'),
    path('users', views.users, name='users'),
    path('ledger', views.ledger, name='ledger'),
    path('userdetails/<int:id>/', views.userdetails, name='userdetails'),
    path('updateuser/<int:id>/', views.updateuser, name='updateuser'),
    path('applications', views.applications, name='applications'),
    path('i18n/', include('django.conf.urls.i18n')),
]
