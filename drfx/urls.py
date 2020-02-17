from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='www')),
    path('api/v1/', include('api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('docs/', include_docs_urls(title='mulysa docs')),
    path('www/', include('www.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
]
