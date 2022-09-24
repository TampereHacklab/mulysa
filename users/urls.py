from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"", views.UserViewSet)
router.register(r"banktransaction", views.BankTransactionAggregateViewSet, basename='banktransaction')

urlpatterns = [
    path("", include(router.urls)),
]
