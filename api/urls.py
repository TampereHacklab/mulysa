from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'access', views.AccessViewSet, basename='access')


urlpatterns = [
    path('auth/', include('rest_auth.urls')),
    path('auth/registration/', include('rest_auth.registration.urls')),
    path('users/', include('users.urls')),
    path('', include(router.urls))
]
