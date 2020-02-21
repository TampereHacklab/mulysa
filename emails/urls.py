from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("<int:epoch>/<slug:subject>", login_required(TemplateView.as_view(template_name="email.html")), name="email"),
]
