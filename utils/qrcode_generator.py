import segno
from io import BytesIO


def generate_epc_qr_code_svg(
    bic: str,
    beneficiary_name: str,
    iban: str,
    amount: float,
    reference: str = "",
    message: str = "",
    purpose: str = "",
) -> str:
    """
    Creates a EPC-compliant QR code that pre-fills payment information
    Args:
        bic: Bank Identifier Code (e.g., 'NDEAFIHH' for Nordea)
        beneficiary_name: Payment receiver name (max 70 characters)
        iban: International Bank Account Number (spaces will be removed)
        amount: Payment amount in euros eg. 35
        reference: Finnish reference number (max 35 chars, goes to 'Viite' field)
        message: Optional payment message (max 140 chars, only used if no reference)
        purpose: Optional 4-character ISO purpose code
    Returns:
        str: SVG markup ready for HTML rendering
    """
    # Clean and format input data
    iban_clean = iban.replace(" ", "")
    amount_formatted = f"EUR{amount:.2f}"

    # Each line represents one field in the EPC structure
    epc_data_fields = [
        "BCD",  # 1: Service tag (constant)
        "001",  # 2: Version
        "1",  # 3: Character set (1 = UTF-8)
        "SCT",  # 4: Identification (SEPA Credit Transfer)
        bic,  # 5: BIC of beneficiary bank
        beneficiary_name[:70],  # 6: Beneficiary name (max 70 chars)
        iban_clean,  # 7: Beneficiary account (IBAN without spaces)
        amount_formatted,  # 8: Amount in EUR with 2 decimals
        purpose[:4] if purpose else "",  # 9: Purpose code (optional, max 4 chars)
        reference.strip()[:35] if reference else "",  # 10: Reference (structured)
        (
            "" if reference else message.strip()[:140]
        ),  # 11: Unstructured message if no ref
    ]

    epc_payload = "\n".join(epc_data_fields)

    qr_code = segno.make(epc_payload, error="m", mode="byte")

    svg_buffer = BytesIO()

    qr_code.save(svg_buffer, kind="svg", scale=6, border=4, xmldecl=False, svgns=False)

    return svg_buffer.getvalue().decode("utf-8")
