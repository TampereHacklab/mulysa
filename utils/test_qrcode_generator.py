from django.test import TestCase
from utils.qrcode_generator import generate_epc_qr_code_svg


class QRCodeGeneratorTests(TestCase):
    """Test for basic svg functionality for EPC QR code generation for bank payments."""

    def test_generates_valid_svg(self):
        svg = generate_epc_qr_code_svg(
            bic="ABCDEF",
            beneficiary_name="Tampere Hacklab ry",
            iban="FI2112345654321111",
            amount=35.00,
            reference="123456",
        )
        self.assertIn("<svg", svg)
        self.assertIn("</svg>", svg)

        self.assertIsInstance(svg, str)
        self.assertGreater(len(svg), 100)
