from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.reservation_views import (
    StorageViewSet,
    StorageUnitViewSet,
    ReservationViewSet,
)
from .views.admin_views import StorageAdminViewSet
from .views.frontend_views import reservation_table

router = DefaultRouter()
router.register(r"services", StorageViewSet, basename="service")
router.register(r"units", StorageUnitViewSet, basename="unit")
router.register(r"reservations", ReservationViewSet, basename="reservation")
router.register(r"admin/storage", StorageAdminViewSet, basename="storage-admin")

urlpatterns = [
    path("api/", include(router.urls)),
    path("", reservation_table, name="reservation_table"),
]
