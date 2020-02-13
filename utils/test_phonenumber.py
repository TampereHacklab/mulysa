import unittest

from . import phonenumber


class TestPhoneNumber(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(phonenumber.normalize_number("044055066"), "+35844055066")
