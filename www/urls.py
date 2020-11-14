from django.urls import include, path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path("", TemplateView.as_view(template_name="www/index.html")),
    path("", include("django.contrib.auth.urls")),
    path("index", TemplateView.as_view(template_name="www/index.html"), name="index"),
    path("register", views.register, name="register"),
    path("dataimport", views.dataimport, name="dataimport"),
    path("dataexport", views.dataexport, name="dataexport"),
    path("users", views.users, name="users"),
    path("users/create", views.createuser, name="users/create"),
    path("ledger", views.ledger, name="ledger"),
    path("custominvoices", views.custominvoices, name="custominvoices"),
    path("userdetails/<int:id>/", views.userdetails, name="userdetails"),
    path("usersettings/<int:id>/", views.usersettings, name="usersettings"),
    path(
        "usersettings/<int:id>/claim_nfc/<str:cardid>",
        views.claim_nfc,
        name="claim_nfc",
    ),
    path(
        "usersettings/<int:id>/subscribe_service/<int:serviceid>",
        views.subscribe_service,
        name="subscribe_service",
    ),
    path(
        "usersettings/<int:id>/unsubscribe_service/<int:serviceid>",
        views.unsubscribe_service,
        name="unsubscribe_service",
    ),
    path("custominvoice", views.custominvoice, name="custominvoice"),
    path(
        "custominvoice/<str:action>/<int:invoiceid>/",
        views.custominvoice_action,
        name="custominvoice_action",
    ),
    path("updateuser/<int:id>/", views.updateuser, name="updateuser"),
    path("applications", views.applications, name="applications"),
    path(
        "applications/<int:application_id>/<str:operation>",
        views.application_operation,
        name="application_operation",
    ),
    path("banktransaction/<int:banktransactionid>/", views.banktransaction_view, name="banktransaction-view"),
    path("i18n/", include("django.conf.urls.i18n")),
]
