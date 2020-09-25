import unittest
import io

from django.core.files.uploadedfile import SimpleUploadedFile

from .dataimport import DataImport
from users.models import BankTransaction


class TestTitoImporter(unittest.TestCase):
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
        BankTransaction.objects.all().delete()
        data = self._getbasetitodata()
        dataline = "".join(data.values())
        lines = io.BytesIO(b"header\n" + dataline.encode())
        results = DataImport.import_tito(lines)
        self.assertDictEqual(
            results, {"imported": 1, "exists": 0, "error": 0, "failedrows": []}
        )
        self.assertEqual(BankTransaction.objects.first().reference_number, data['viite'].strip().strip("0"))

    def test_tito_import_wrong_length(self):
        BankTransaction.objects.all().delete()
        data = self._getbasetitodata()
        # remove one character from the end
        dataline = "".join(data.values())[:-1]
        print(len(dataline))
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
        BankTransaction.objects.all().delete()
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


class TestHolviImporter(unittest.TestCase):
    def test_holvi_import(self):
        xls = open("utils/holvi-account-test-statement.xls", "rb")
        name = xls.name
        data = xls.read()
        res = DataImport.import_holvi(SimpleUploadedFile(name, data))
        self.assertDictEqual(
            res, {"imported": 2, "exists": 0, "error": 0, "failedrows": []}
        )

        # and again to test that it found the same rows
        res = DataImport.import_holvi(SimpleUploadedFile(name, data))
        self.assertDictEqual(
            res, {"imported": 0, "exists": 2, "error": 0, "failedrows": []}
        )

    def tearDown(self):
        BankTransaction.objects.all().delete()
