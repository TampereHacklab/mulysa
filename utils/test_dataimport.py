import io
from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from .dataimport import DataImport
from users import models


class TestServiceSubscriptionContinuationWithImport(TestCase):
    def setUp(self):
        # one active user with subscription that is about to go overdue
        self.user = get_user_model().objects.create_customuser(
            first_name="FirstName",
            last_name="LastName",
            email="user1@example.com",
            birthday=timezone.now(),
            municipality="City",
            nick="user1",
            phone="+358123123",
        )
        self.memberservice = models.MemberService.objects.create(
            name="TestService",
            cost=10,
            days_per_payment=30,
        )
        self.servicesubscription = models.ServiceSubscription.objects.create(
            user=self.user,
            service=self.memberservice,
            state=models.ServiceSubscription.OVERDUE,
            # payment is over two "days_per_payment"
            paid_until=timezone.now().date() + timedelta(days=-50),
            reference_number="11112",
        )

    def _createTitodata(self, date, amount):
        datestr = date.strftime("%y%m%d")
        amount = amount * 100
        return {
            "aineistotunnus": "T",
            "tietuetunnus": "10",
            "tietueenpituus": "188",
            "tapahtumannumero": "1".rjust(6, "0"),
            "arkistointitunnus": datestr.rjust(18, "0"),
            "kirjauspaiva": datestr,
            "arvopaiva": datestr,
            "maksupaiva": datestr,
            "tapahtumatunnus": "1",  # 1 pano, 2 otto, 3 panon korjaus, 4 oton korjaus
            "kirjausselitekoodi": "719",
            "kirjausselite": "Viitemaksu".ljust(35),
            "rahamaaraetumerkki": "+",
            "rahamaara": str(amount).rjust(18, "0"),  # two decimals
            "kuittikoodi": " ",  # assumed to be empty
            "valitystapa": " ",  # assumed to be empty
            "saaja_maksaja": "TESTI HENKIL[".ljust(35),
            "nimen_lahde": "J",  # no idea what this means
            "saajan_tili": "".ljust(14),  # seems to be empty when money comes in
            "saajan_tili_muuttunut": " ",  # yup, no idea
            "viite": "11112".rjust(20, "0"),
            "lomakkeen_numero": "".ljust(8),  # yup, no idea again
            "tasotunnus": " ",  # empty means that it is really in the account :)
        }

    def test_user_gets_more_time(self):
        paid_delta = -50
        # starts of as overdue
        self.assertEqual(self.servicesubscription.state, models.ServiceSubscription.OVERDUE)
        self.assertEqual(self.servicesubscription.paid_until, timezone.now().date() + timedelta(days=paid_delta))

        # makes one payment two days ago, still overdue but the date has changed
        data = self._createTitodata(timezone.now().date() + timedelta(days=-2), 10)
        dataline = "".join(data.values())
        lines = io.BytesIO(b"header\n" + dataline.encode())
        results = DataImport.import_tito(lines)
        self.assertDictEqual(
            results, {"imported": 1, "exists": 0, "error": 0, "failedrows": []}
        )
        paid_delta += 30

        self.servicesubscription.refresh_from_db()
        self.assertEqual(self.servicesubscription.state, models.ServiceSubscription.OVERDUE)
        self.assertEqual(self.servicesubscription.paid_until, timezone.now().date() + timedelta(days=paid_delta))

        # makes another payment yesterday, state PAID and date in future
        data = self._createTitodata(timezone.now().date() + timedelta(days=-1), 10)
        dataline = "".join(data.values())
        lines = io.BytesIO(b"header\n" + dataline.encode())
        results = DataImport.import_tito(lines)
        self.assertDictEqual(
            results, {"imported": 1, "exists": 0, "error": 0, "failedrows": []}
        )
        paid_delta += 30

        self.servicesubscription.refresh_from_db()
        self.assertEqual(self.servicesubscription.state, models.ServiceSubscription.ACTIVE)
        self.assertEqual(self.servicesubscription.paid_until, timezone.now().date() + timedelta(days=paid_delta))

    def tearDown(self):
        self.user.delete()
        self.memberservice.delete()
        self.servicesubscription.delete()
        models.BankTransaction.objects.all().delete()

class TestTitoImporter(TestCase):
    def _getbasetitodata(self):
        """
        TODO: this should really be its own class that knows how to
        generate the real line data. for now this will have to do
        if you change the values remember to keep the length correct
        """
        return {
            "aineistotunnus": "T",
            "tietuetunnus": "10",
            "tietueenpituus": "188",
            "tapahtumannumero": "1".rjust(6, "0"),
            "arkistointitunnus": "ABC".rjust(18, "0"),
            "kirjauspaiva": "200916",
            "arvopaiva": "200916",
            "maksupaiva": "200916",
            "tapahtumatunnus": "1",  # 1 pano, 2 otto, 3 panon korjaus, 4 oton korjaus
            "kirjausselitekoodi": "719",
            "kirjausselite": "Viitemaksu".ljust(35),
            "rahamaaraetumerkki": "+",
            "rahamaara": "12300".rjust(18, "0"),  # two decimals
            "kuittikoodi": " ",  # assumed to be empty
            "valitystapa": " ",  # assumed to be empty
            "saaja_maksaja": "TESTI HENKIL[".ljust(35),
            "nimen_lahde": "J",  # no idea what this means
            "saajan_tili": "".ljust(14),  # seems to be empty when money comes in
            "saajan_tili_muuttunut": " ",  # yup, no idea
            "viite": "11112".rjust(20, "0"),
            "lomakkeen_numero": "".ljust(8),  # yup, no idea again
            "tasotunnus": " ",  # empty means that it is really in the account :)
        }

    def test_tito_import_generated_data(self):
        """
        Test that the generated data above works
        """
        models.BankTransaction.objects.all().delete()
        data = self._getbasetitodata()
        dataline = "".join(data.values())
        lines = io.BytesIO(b"header\n" + dataline.encode())
        results = DataImport.import_tito(lines)
        self.assertDictEqual(
            results, {"imported": 1, "exists": 0, "error": 0, "failedrows": []}
        )
        self.assertEqual(models.BankTransaction.objects.first().reference_number, data['viite'].strip().strip("0"))

    def test_tito_import_wrong_length(self):
        models.BankTransaction.objects.all().delete()
        data = self._getbasetitodata()
        # remove one character from the end
        dataline = "".join(data.values())[:-1]
        lines = io.BytesIO(b"header\n" + dataline.encode())
        results = DataImport.import_tito(lines)
        self.assertDictContainsSubset({"imported": 0, "exists": 0, "error": 1}, results)

    def test_tito_import_empty_file(self):
        """
        empty file
        """
        data = io.BytesIO(b"")
        results = DataImport.import_tito(data)
        self.assertDictEqual(
            results, {"imported": 0, "exists": 0, "error": 0, "failedrows": []}
        )

    def test_tito_import_invalid_file(self):
        """
        random data
        """
        data = io.BytesIO(b"foo\nbar")
        results = DataImport.import_tito(data)
        self.assertDictEqual(
            results,
            {
                "imported": 0,
                "exists": 0,
                "error": 1,
                "failedrows": ["bar (Empty line or not starting with T)"],
            },
        )

    def test_tito_import_production_data(self):
        """
        this data is almost direct from real world data, some values have just
        been changed so that the persons identiy is not compromised
        """
        models.BankTransaction.objects.all().delete()
        data = io.BytesIO(
            b"header\nT101880000011111111111111111112009252009252009251"
            b"710Viitemaksu                         +000000000000012300  "
            b"TESTI HENKIL[                      J               "
            b"00000000000000011112         "
        )
        results = DataImport.import_tito(data)
        self.assertDictEqual(
            results, {"imported": 1, "exists": 0, "error": 0, "failedrows": []}
        )

        # and same again to see that it found it again
        data = io.BytesIO(
            b"header\nT101880000011111111111111111112009252009252009251"
            b"710Viitemaksu                         +000000000000012300  "
            b"TESTI HENKIL[                      J               "
            b"00000000000000011112         "
        )
        results = DataImport.import_tito(data)
        self.assertDictEqual(
            results, {"imported": 0, "exists": 1, "error": 0, "failedrows": []}
        )

    def test_tito_cents(self):
        models.BankTransaction.objects.all().delete()
        data = self._getbasetitodata()
        # with 45 cents
        data['rahamaara'] = "12345".rjust(18, "0")
        dataline = "".join(data.values())
        lines = io.BytesIO(b"header\n" + dataline.encode())
        results = DataImport.import_tito(lines)
        self.assertDictEqual(
            results, {"imported": 1, "exists": 0, "error": 0, "failedrows": []}
        )
        self.assertEqual(models.BankTransaction.objects.first().reference_number, data['viite'].strip().strip("0"))
        self.assertEqual(models.BankTransaction.objects.first().amount, Decimal('123.45'), 'Check decimals')

class TestHolviImporter(TestCase):
    def test_holvi_import_2022_format(self):
        """
        Test import with data format from 2022-05-18

        Uses same fields but XLSX file format.
        """
        models.BankTransaction.objects.all().delete()
        xls = open("utils/holvi-account-test-statement-2022-05.xlsx", "rb")
        name = xls.name
        data = xls.read()
        res = DataImport.import_holvi(SimpleUploadedFile(name, data))
        self.assertDictEqual(
            res, {"imported": 5, "exists": 0, "error": 0, "failedrows": []}
        )

        # and again to test that it found the same rows
        res = DataImport.import_holvi(SimpleUploadedFile(name, data))
        self.assertDictEqual(
            res, {"imported": 0, "exists": 5, "error": 0, "failedrows": []}
        )

    def test_holvi_cents(self):
        models.BankTransaction.objects.all().delete()
        xls = open("utils/holvi-account-test-statement-2022-05.xlsx", "rb")
        name = xls.name
        data = xls.read()
        res = DataImport.import_holvi(SimpleUploadedFile(name, data))
        self.assertDictEqual(
            res, {"imported": 5, "exists": 0, "error": 0, "failedrows": []}
        )
        # third row on the test file
        transaction = models.BankTransaction.objects.get(archival_reference='0b914e1f528d902e6fe1ee7ff792ce5f')
        self.assertEqual(transaction.amount, Decimal('-7.44'), 'Check decimals')

    def tearDown(self):
        models.BankTransaction.objects.all().delete()
