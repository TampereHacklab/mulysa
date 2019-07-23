from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='www/index.html')),
    path('index', TemplateView.as_view(template_name='www/index.html'), name='index'),
    path('register', views.register, name='register'),
    path('dataimport', views.dataimport, name='dataimport'),
    path('users', views.users, name='users'),
    path('user/<int:id>/', views.user, name='user'),
    path('applications', views.applications, name='applications'),
]
