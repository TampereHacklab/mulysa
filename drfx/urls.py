from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from oauth2_provider.urls import app_name, base_urlpatterns, oidc_urlpatterns

from rest_framework.schemas import get_schema_view

favicon_view = RedirectView.as_view(url="/static/www/favicon.ico", permanent=True)
schema_view = get_schema_view(title="mulysa docs")

urlpatterns = [
    path("favicon.ico", favicon_view),
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="www")),
    path("api/v1/", include("api.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("docs/", schema_view),
    path("www/", include("www.urls")),
    path("email/", include("emails.urls")),
    path(
        "o/",
        include(
            (base_urlpatterns + oidc_urlpatterns, app_name), namespace="oauth2_provider"
        ),
    ),
]
