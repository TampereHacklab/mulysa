from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='www/index.html')),
    path('register', views.register),
    path('dataimport', views.dataimport),
    path('users', views.users),
]
