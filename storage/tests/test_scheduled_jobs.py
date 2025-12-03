import datetime
from decimal import Decimal
from django.utils import timezone
from django.test import TestCase

from users.models import CustomUser
from storage.models import StorageReservation, StorageUnit, StorageService
from storage.utils.expire_pending_reservations import expire_pending_reservations
from storage.utils.complete_reservations import complete_finished_reservations


class TestScheduledJobs(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )

        self.storage = StorageService.objects.create(
            name="Test Storage", pending_payment_days=5
        )

        self.unit = StorageUnit.objects.create(
            name="Test Unit",
            service=self.storage,
            price_per_month=Decimal("100.00"),
            max_rental_months=12,
        )

        self.today = timezone.now().date()

    def test_expire_only_if_pending_until_is_past(self):
        """Pending reservation expires only if pending_until < today."""
        old_pending = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.PENDING,
            pending_until=self.today - datetime.timedelta(days=1),
            start_date=self.today,
            end_date=self.today + datetime.timedelta(days=30),
        )
        on_deadline = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.PENDING,
            pending_until=self.today,  # SHOULD NOT EXPIRE
            start_date=self.today,
            end_date=self.today + datetime.timedelta(days=30),
        )
        future_pending = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.PENDING,
            pending_until=self.today + datetime.timedelta(days=1),
            start_date=self.today,
            end_date=self.today + datetime.timedelta(days=30),
        )

        expire_pending_reservations()

        old_pending.refresh_from_db()
        on_deadline.refresh_from_db()
        future_pending.refresh_from_db()

        self.assertEqual(old_pending.status, StorageReservation.EXPIRED)
        self.assertEqual(on_deadline.status, StorageReservation.PENDING)
        self.assertEqual(future_pending.status, StorageReservation.PENDING)

    def test_expire_does_not_touch_non_pending(self):
        """Non-pending reservations must remain unchanged."""
        active = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.ACTIVE,
            pending_until=self.today - datetime.timedelta(days=10),
            start_date=self.today,
            end_date=self.today + datetime.timedelta(days=30),
        )
        completed = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.COMPLETED,
            pending_until=self.today - datetime.timedelta(days=10),
            start_date=self.today - datetime.timedelta(days=60),
            end_date=self.today - datetime.timedelta(days=1),
        )
        already_expired = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.EXPIRED,
            pending_until=self.today - datetime.timedelta(days=10),
            start_date=self.today,
            end_date=self.today + datetime.timedelta(days=30),
        )

        expire_pending_reservations()

        active.refresh_from_db()
        completed.refresh_from_db()
        already_expired.refresh_from_db()

        self.assertEqual(active.status, StorageReservation.ACTIVE)
        self.assertEqual(completed.status, StorageReservation.COMPLETED)
        self.assertEqual(already_expired.status, StorageReservation.EXPIRED)

    def test_pending_without_pending_until_is_not_expired(self):
        """If pending_until is missing, reservation must not expire."""
        r = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.PENDING,
            pending_until=None,
            start_date=self.today,
            end_date=self.today + datetime.timedelta(days=30),
        )

        expire_pending_reservations()

        r.refresh_from_db()
        self.assertEqual(r.status, StorageReservation.PENDING)

    def test_complete_active_only_if_end_date_in_past(self):
        """Active reservation should be completed only if end date is passed."""
        old_active = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.ACTIVE,
            start_date=self.today - datetime.timedelta(days=60),
            end_date=self.today - datetime.timedelta(days=1),
        )
        ends_today = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.ACTIVE,
            start_date=self.today - datetime.timedelta(days=30),
            end_date=self.today,  # SHOULD NOT COMPLETE
        )
        future_end = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.ACTIVE,
            start_date=self.today - datetime.timedelta(days=10),
            end_date=self.today + datetime.timedelta(days=10),
        )

        complete_finished_reservations()

        old_active.refresh_from_db()
        ends_today.refresh_from_db()
        future_end.refresh_from_db()

        self.assertEqual(old_active.status, StorageReservation.COMPLETED)
        self.assertEqual(ends_today.status, StorageReservation.ACTIVE)
        self.assertEqual(future_end.status, StorageReservation.ACTIVE)

    def test_complete_does_not_touch_non_active(self):
        """Non-active reservations must remain unchanged"""
        pending = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.PENDING,
            start_date=self.today - datetime.timedelta(days=30),
            end_date=self.today - datetime.timedelta(days=1),
        )
        expired = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.EXPIRED,
            start_date=self.today - datetime.timedelta(days=30),
            end_date=self.today - datetime.timedelta(days=1),
        )
        completed = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.COMPLETED,
            start_date=self.today - datetime.timedelta(days=60),
            end_date=self.today - datetime.timedelta(days=30),
        )

        complete_finished_reservations()

        pending.refresh_from_db()
        expired.refresh_from_db()
        completed.refresh_from_db()

        self.assertEqual(pending.status, StorageReservation.PENDING)
        self.assertEqual(expired.status, StorageReservation.EXPIRED)
        self.assertEqual(completed.status, StorageReservation.COMPLETED)

    def test_both_jobs_together_do_not_conflict(self):
        """Expired must not later become completed, and vice versa."""
        old_pending = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.PENDING,
            pending_until=self.today - datetime.timedelta(days=10),
            start_date=self.today - datetime.timedelta(days=40),
            end_date=self.today - datetime.timedelta(days=5),
        )
        old_active = StorageReservation.objects.create(
            user=self.user,
            unit=self.unit,
            status=StorageReservation.ACTIVE,
            start_date=self.today - datetime.timedelta(days=40),
            end_date=self.today - datetime.timedelta(days=5),
        )

        # Run both in same order as daily job
        expire_pending_reservations()
        complete_finished_reservations()

        old_pending.refresh_from_db()
        old_active.refresh_from_db()

        self.assertEqual(old_pending.status, StorageReservation.EXPIRED)
        self.assertEqual(old_active.status, StorageReservation.COMPLETED)
