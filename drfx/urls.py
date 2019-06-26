from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('api/v1/', include('api.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('docs/', include_docs_urls(title='mulysa docs'))
]

if settings.DEBUG:
    urlpatterns += [
        path('admin/', admin.site.urls),
    ]
