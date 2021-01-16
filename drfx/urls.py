from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(url="www")),
    path("api/v1/", include("api.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("docs/", include_docs_urls(title="mulysa docs")),
    path("www/", include("www.urls")),
    path("email/", include("emails.urls")),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
