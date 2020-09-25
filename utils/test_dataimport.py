import unittest
import io

from .dataimport import DataImport


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
    # check above and try to make the same for Holvi ;)
    def test_holvi_import(self):
        pass