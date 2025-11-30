from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from utils.qrcode_generator import generate_epc_qr_code_svg

register = template.Library()

@register.simple_tag
def payment_qr_code(subscription, bank_iban, bank_bic, bank_name):
    """
    Generate a payment QR code for a service subscription.
    Args:
        subscription: ServiceSubscription instance with service cost and reference
        bank_iban: Beneficiary's IBAN account number
        bank_bic: Beneficiary's Bank Identifier Code
        bank_name: Name of the payment receiver organization
    Returns:
        SafeString: SVG markup for the QR code, or error message if generation fails
    """
    try:
        # Extract payment information from subscription
        payment_amount = subscription.service.cost
        reference_number = subscription.reference_number or ""
        service_description = subscription.service.name

        qr_code_svg = generate_epc_qr_code_svg(
            bic=bank_bic,
            beneficiary_name=bank_name,
            iban=bank_iban,
            amount=payment_amount,
            reference=reference_number,
            message=service_description,
        )

        return mark_safe(qr_code_svg)

    except Exception as error:
        # Return user-friendly error message if qr fals
        error_html = f'<p class="text-danger">{_("QR code generation failed")}: {str(error)}</p>'
        return mark_safe(error_html)
