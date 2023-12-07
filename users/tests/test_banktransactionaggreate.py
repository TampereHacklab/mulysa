from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode

from rest_framework import status
from rest_framework.test import APITestCase

from users import models


class BankAggreagetApiTests(APITestCase):
    """
    Tests for showing statistics of bank transactions
    """

    def setUp(self):
        """
        Generate few banktransactions for testing
        """
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        # for these dates, generate 10 deposits and withdravals for each day
        start_date = date(2022, 1, 1)
        end_date = date(2022, 1, 11)
        for single_date in self.daterange(start_date, end_date):
            for amount in range(1, 11):
                models.BankTransaction.objects.create(
                    archival_reference=f"{single_date}_deposit_{amount}",
                    date=single_date,
                    amount=amount,
                )
                models.BankTransaction.objects.create(
                    archival_reference=f"{single_date}_withdraval_{amount}",
                    date=single_date,
                    amount=amount * -1,
                )

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def test_get_banktransactionaggregatedata_not_loggedin(self):
        """
        only logged in users can get the data
        """
        url = reverse("banktransactionaggregate-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_banktransactionaggregatedata(self):
        """
        aggregated data
        """
        self.client.force_login(user=self.user)
        url = reverse("banktransactionaggregate-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 10)

        # check first day data
        firstDay = response.data[0]
        self.assertEqual(firstDay["withdrawals"], -55)
        self.assertEqual(firstDay["deposits"], 55)
        self.assertEqual(firstDay["deposits"] + firstDay["withdrawals"], 0)
        self.assertEqual(firstDay["aggregatedate"], "2022-01-01")

        # last day data is similar
        lastDay = response.data[-1]
        self.assertEqual(lastDay["withdrawals"], -55)
        self.assertEqual(lastDay["deposits"], 55)
        self.assertEqual(lastDay["deposits"] + lastDay["withdrawals"], 0)
        self.assertEqual(lastDay["aggregatedate"], "2022-01-10")

    def test_get_banktransactionaggregatedata_filtered(self):
        """
        aggregated data
        """
        self.client.force_login(user=self.user)
        urlbase = reverse("banktransactionaggregate-list")
        qparams = urlencode({"date__gte": "2022-01-01", "date__lte": "2022-01-01"})
        url = f"{urlbase}?{qparams}"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # only one day result
        self.assertEqual(len(response.data), 1)
        firstDay = response.data[0]
        self.assertEqual(firstDay["withdrawals"], -55)
        self.assertEqual(firstDay["deposits"], 55)
        self.assertEqual(firstDay["deposits"] + firstDay["withdrawals"], 0)
        self.assertEqual(firstDay["aggregatedate"], "2022-01-01")

    def tearDown(self):
        models.CustomUser.objects.all().delete()
        models.BankTransaction.objects.all().delete()
