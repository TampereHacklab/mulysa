import unittest

from . import stringutils


class TestStripTagsAndWhiteSpace(unittest.TestCase):
    """
    Simple test cases for stringutils
    """

    def test_strip(self):
        s = """

        <h1>Foo</h1>



        <p>Bar</p>

        """
        expected = "Foo\nBar"
        self.assertEqual(stringutils.strip_tags_and_whitespace(s), expected)
