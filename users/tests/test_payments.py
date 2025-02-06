from django.contrib.auth import get_user_model
from django.test import TestCase

from drfx import config
from datetime import date, timedelta
from utils import referencenumber
from utils.businesslogic import BusinessLogic

from users.models import (
    BankTransaction,
    CustomInvoice,
    CustomUser,
    MemberService,
    ServiceSubscription,
)


class PaymentServices(TestCase):
    """
    Tests for payment of services and custom invoices
    """

    parent_ref = referencenumber.generate(123)
    child_ref = referencenumber.generate(456)
    grandchild_ref = referencenumber.generate(789)
    custom_invoice_ref = referencenumber.generate(101112)

    def setUp(self):
        """
        Generate test user, test services and test
        """
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=date.today(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )

        self.grandchild_service = MemberService(
            name="grandchild_service",
            cost=10,
            days_per_payment=70,
            days_bonus_for_first=20,
        )
        self.grandchild_service.save()

        self.child_service = MemberService(
            name="child_service",
            cost=10,
            days_per_payment=60,
            days_bonus_for_first=20,
            pays_also_service=self.grandchild_service,
        )
        self.child_service.save()

        self.parent_service = MemberService(
            name="parent_service",
            cost=30,
            days_per_payment=30,
            days_bonus_for_first=10,
            pays_also_service=self.child_service,
        )
        self.parent_service.save()

        self.parent_subscription = ServiceSubscription(
            user=self.user,
            service=self.parent_service,
            state=ServiceSubscription.ACTIVE,
            reference_number=self.parent_ref,
        )
        self.parent_subscription.save()

        self.child_subscription = ServiceSubscription(
            user=self.user,
            service=self.child_service,
            state=ServiceSubscription.ACTIVE,
            reference_number=self.child_ref,
        )
        self.child_subscription.save()

        self.grandchild_subscription = ServiceSubscription(
            user=self.user,
            service=self.grandchild_service,
            state=ServiceSubscription.ACTIVE,
            reference_number=self.grandchild_ref,
        )
        self.grandchild_subscription.save()

        self.custom_invoice = CustomInvoice(
            reference_number=self.custom_invoice_ref,
            user=self.user,
            days=100,
            amount=120,
            subscription=self.parent_subscription,
        )
        self.custom_invoice.save()

    def test_static_parent_payment(self):
        #
        # First test parent payment pays all services
        #

        amounts = [15, 30, 30, 30, 15]
        # [not_enough_money, extradays, days_per_payment, days_per_payment, not_enough_money]
        e_p_results = [0, 40, 70, 100, 100]
        # virtual_payment = parent.daysleft - parent_days_per_payment + child_days_per_payment
        # [not_enough_money, virtual_payment + extradays,  virtual_payment, virtual_payment, not_enough_money]
        e_c_results = [0, 90, 100, 130, 130]
        # [not_enough_money, virtual_payment + extradays,  virtual_payment<last=last, virtual_payment, not_enough_money]
        e_gc_results = [0, 120, 120, 140, 140]
        refs = [self.parent_ref, self.child_ref, self.grandchild_ref]

        results = self.payment(amounts, refs, self.user)
        self.assertNotEqual(results, False)
        p_results, c_results, gc_results = results

        self.assertEqual(p_results, e_p_results)
        self.assertEqual(c_results, e_c_results)
        self.assertEqual(gc_results, e_gc_results)

        #
        # Then test custom invoice payment with one payment allowed
        #

        amounts = [50, 120, 120, 120, 50]
        refs = [self.custom_invoice_ref, self.child_ref, self.grandchild_ref]
        config.CUSTOM_INVOICE_DYNAMIC_PRICING = False
        config.CUSTOM_INVOICE_ALLOW_MULTIPLE_PAYMENTS = False

        # add custominvoice days from previous test, just one addition possible
        e_p_results = [100, 200, 200, 200, 200]
        e_c_results = [130, 230, 230, 230, 230]
        e_gc_results = [140, 240, 240, 240, 240]

        results = self.payment(amounts, refs, self.user)
        self.assertNotEqual(results, False)
        p_results, c_results, gc_results = results

        self.assertEqual(p_results, e_p_results)
        self.assertEqual(c_results, e_c_results)
        self.assertEqual(gc_results, e_gc_results)

        # remove custominvoices, to easily run paymentfunction
        CustomInvoiceTransactions = BankTransaction.objects.filter(
            reference_number=self.custom_invoice_ref
        )
        for CustomInvoiceTransaction in CustomInvoiceTransactions:
            CustomInvoiceTransaction.delete()
        BusinessLogic.updateuser(self.user)

    def test_dynamic_parent_payment(self):
        #
        # Test parent payment when cost_min is defined
        #
        self.parent_service.cost_min = 15
        self.parent_service.save()
        refs = [self.parent_ref]
        amounts = [10, 15, 30, 15, 10]
        e_p_results = [0, 40, 70, 100, 100]

        results = self.payment(amounts, refs, self.user)
        self.assertNotEqual(results, False)

        p_results = results
        self.assertEqual(p_results, e_p_results)

    def test_child_payment_parent_active(self):
        amounts = [5, 10, 10, 10, 5]
        # [Active parent subscription prevent payment]
        e_results = [0, 0, 0, 0, 0]
        refs = [self.child_ref]
        results = self.payment(amounts, refs, self.user)
        self.assertEqual(results, e_results)

    def test_child_payment_parent_deleted(self):
        amounts = [5, 10, 10, 10, 5]
        # Remove parent subscription
        subscriptions = ServiceSubscription.objects.filter(
            reference_number=self.parent_ref
        )
        subscriptions[0].delete()

        # [not_enough_money, extradays, days_per_payment, days_per_payment, not_enough_money]
        e_results = [0, 80, 140, 200, 200]
        refs = [self.child_ref]
        results = self.payment(amounts, refs, self.user)
        self.assertEqual(results, e_results)

    @staticmethod
    def payment(amounts, refs, user):
        # create payments with reference of refs[0] with amounts[] for user
        # returns days_left for ref after each amount paid
        # eg payment([10, 10, 10],[123, 456, 789, 101],user)
        # returns   [20, 40, 60]
        #           [25, 45, 65]
        #           [30, 50, 70]
        #           [40, 60, 100]
        n = -1
        results = []

        for amount in amounts:
            deltad = timedelta(days=n)
            n += 1
            transaction = BankTransaction(
                reference_number=refs[0],
                archival_reference=refs[0] + n,
                date=date.today() + deltad,
                amount=amount,
                sender=user.first_name,
            )
            transaction.save()
            BusinessLogic.new_transaction(transaction)
            BusinessLogic.updateuser(user)

            results_row = []
            for ref in refs:
                subscriptions = ServiceSubscription.objects.filter(reference_number=ref)
                custominvoices = CustomInvoice.objects.filter(reference_number=ref)

                if len(subscriptions) > 0:
                    for subscription in subscriptions:
                        results_row.append(subscription.days_left())

                elif len(custominvoices) > 0:
                    for custominvoice in custominvoices:
                        results_row.append(custominvoice.subscription.days_left())
                else:
                    return False

            results.append(results_row)
        transposed_results = [
            [results[j][i] for j in range(len(results))] for i in range(len(results[0]))
        ]
        if len(transposed_results) == 1:
            result = [
                transposed_results[0][i] for i in range(len(transposed_results[0]))
            ]
            return result
        else:
            return transposed_results

    def tearDown(self):
        CustomInvoice.objects.all().delete()
        CustomUser.objects.all().delete()
        MemberService.objects.all().delete()
        ServiceSubscription.objects.all().delete()
        BankTransaction.objects.all().delete()
