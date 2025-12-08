from decimal import Decimal
from django.test import TestCase, RequestFactory
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from users.models import BankTransaction, CustomUser
from storage.models import (
    StorageReservation,
    StorageUnit,
    StorageService,
    StoragePayment,
)
from storage.serializers.reservation_serializers import (
    StorageReservationCreateSerializer,
)
from utils.businesslogic import BusinessLogic


class TestPaymentProcessing(TestCase):
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

        # Create test unit and reservation
        self.unit = StorageUnit.objects.create(
            name="Test Unit",
            service=self.storage,
            price_per_month=Decimal("50.00"),
            max_rental_months=6,
        )

        # Simulate DRF serializer creation (like real UI)
        factory = RequestFactory()
        request = factory.post("/api/v1/storage/reservations/")
        request.user = self.user

        serializer = StorageReservationCreateSerializer(
            data={"unit": self.unit.id, "duration_months": 2},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        self.reservation = serializer.save(
            user=self.user, reference_number="123456", status=StorageReservation.PENDING
        )

    def test_payment_updates_reservation(self):
        """Pay for 3 months and verify reservation updates correctly."""
        tx = BankTransaction.objects.create(
            reference_number="123456",
            amount=Decimal("150.00"),
            date=timezone.now().date(),
        )

        BusinessLogic.new_transaction(tx)

        updated = StorageReservation.objects.get(id=self.reservation.id)

        # Check reservation state
        self.assertEqual(updated.status, StorageReservation.ACTIVE)
        self.assertEqual(updated.total_paid_months, 3)
        self.assertIsNotNone(updated.paid_at)
        self.assertEqual(updated.user, self.user)

        # Payment record
        payment = StoragePayment.objects.filter(reservation=updated).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.months, 3)
        self.assertEqual(payment.amount, Decimal("150.00"))

    def test_payment_respects_max_duration(self):
        """Paying more than allowed max duration should only extend to the limit."""
        # Reservation starts with 5 months paid
        self.reservation.total_paid_months = 5
        self.reservation.end_date = self.reservation.start_date + relativedelta(
            months=5
        )
        self.reservation.save()

        # Pay 200€ (4 months worth)
        tx = BankTransaction.objects.create(
            reference_number="123456",
            amount=Decimal("200.00"),
            date=timezone.now().date(),
        )

        BusinessLogic.new_transaction(tx)

        updated = StorageReservation.objects.get(id=self.reservation.id)

        # Total months should not exceed 6 (max_rental_months)
        self.assertEqual(updated.total_paid_months, 6)

        expected_end = self.reservation.start_date + relativedelta(months=6)
        self.assertEqual(updated.end_date, expected_end)

        self.assertEqual(updated.status, StorageReservation.ACTIVE)

        # Last payment should only cover 1 month
        payment = updated.storagepayment_set.last()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.months, 1)

    def test_payment_too_small_to_cover_one_month(self):
        """Payment smaller than price_per_month must be ignored."""
        tx = BankTransaction.objects.create(
            reference_number="123456",
            amount=Decimal("10.00"),  # less than 50€/month
            date=timezone.now().date(),
        )

        BusinessLogic.new_transaction(tx)

        updated = StorageReservation.objects.get(id=self.reservation.id)
        self.assertEqual(updated.total_paid_months, 0)
        self.assertEqual(updated.storagepayment_set.count(), 0)

    def test_partial_month_payment_not_allowed(self):
        """Reservation can only be extended by full months."""
        tx = BankTransaction.objects.create(
            reference_number="123456",
            amount=Decimal("75.00"),  # 1.5 months → should count as 1
            date=timezone.now().date(),
        )

        BusinessLogic.new_transaction(tx)

        updated = StorageReservation.objects.get(id=self.reservation.id)
        self.assertEqual(updated.total_paid_months, 1)

        last_payment = updated.storagepayment_set.last()
        self.assertEqual(last_payment.months, 1)

    def test_payment_for_expired_reservation_does_nothing(self):
        """Expired reservation should not reactivate when paid."""
        self.reservation.status = StorageReservation.EXPIRED
        self.reservation.save()

        tx = BankTransaction.objects.create(
            reference_number="123456",
            amount=Decimal("50.00"),
            date=timezone.now().date(),
        )

        BusinessLogic.new_transaction(tx)

        updated = StorageReservation.objects.get(id=self.reservation.id)
        self.assertEqual(updated.total_paid_months, 0)
        self.assertEqual(updated.status, StorageReservation.EXPIRED)
