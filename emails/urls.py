from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, ListView

from . import models

urlpatterns = [
    path(
        "",
        login_required(
            ListView.as_view(
                paginate_by=50,
                queryset=models.Email.objects.filter(sent__isnull=False).order_by(
                    "-sent"
                ),
            )
        ),
    ),
    path(
        "<int:epoch>/<slug:slug>",
        login_required(
            DetailView.as_view(queryset=models.Email.objects.filter(sent__isnull=False))
        ),
        name="email",
    ),
]
