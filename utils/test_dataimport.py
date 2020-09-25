import unittest
import io

from django.core.files.uploadedfile import SimpleUploadedFile

from .dataimport import DataImport
from users.models import BankTransaction


class TestTitoImporter(unittest.TestCase):
    def test_tito_import_empty_file(self):
        data = io.BytesIO(b"")
        results = DataImport.import_tito(data)
        self.assertDictEqual(results, {'imported': 0, 'exists': 0, 'error': 0, 'failedrows': []})

    def test_tito_import_invalid_file(self):
        data = io.BytesIO(b"foo\nbar")
        results = DataImport.import_tito(data)
        self.assertDictEqual(results, {'imported': 0, 'exists': 0, 'error': 1, 'failedrows': ['bar (Empty line or not starting with T)']})

    def test_tito_import_one_ok(self):
        data = io.BytesIO(b"foo\nbar")
        results = DataImport.import_tito(data)
        self.assertDictEqual(results, {'imported': 0, 'exists': 0, 'error': 1, 'failedrows': ['bar (Empty line or not starting with T)']})


class TestHolviImporter(unittest.TestCase):
    def test_holvi_import(self):
        xls = open('utils/holvi-account-test-statement.xls', 'rb')
        name = xls.name
        data = xls.read()
        res = DataImport.import_holvi(SimpleUploadedFile(name, data))
        self.assertDictEqual(res, {'imported': 2, 'exists': 0, 'error': 0, 'failedrows': []})

        # and again to test that it found the same rows
        res = DataImport.import_holvi(SimpleUploadedFile(name, data))
        self.assertDictEqual(res, {'imported': 0, 'exists': 2, 'error': 0, 'failedrows': []})

    def tearDown(self):
        BankTransaction.objects.all().delete()
