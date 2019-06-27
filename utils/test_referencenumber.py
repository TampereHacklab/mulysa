import unittest

from . import referencenumber


class TestReferenceNumber(unittest.TestCase):
    def test_generate(self):
        self.assertEqual(referencenumber.generate(123), 1232, 'generated correct reference number')

        with self.assertRaises(ValueError):
            referencenumber.generate(1)

    def test_validate(self):
        with self.assertRaises(ValueError):
            referencenumber.validate(123)

        with self.assertRaises(ValueError):
            referencenumber.validate(111111)

        self.assertIsNone(referencenumber.validate(1232))

        self.assertTrue(referencenumber.isvalid(1232))
        self.assertFalse(referencenumber.isvalid(1233))

    def test_random(self):
        with self.assertRaises(ValueError):
            referencenumber.generate_random(200, 100)

        self.assertIsNotNone(referencenumber.generate_random(100, 200))

    def test_format(self):
        n = referencenumber.generate(1111111111)
        self.assertEqual(referencenumber.format(n), '1 11111 11110')