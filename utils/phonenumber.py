import phonenumbers


def normalize_number(number):
    """
    normalize number to E.164 format.
    NOTE: if parsing fails, default to finland
    """
    parsed = None
    try:
        parsed = phonenumbers.parse(number)
    except phonenumbers.NumberParseException:
        parsed = phonenumbers.parse(number, "FI")

    if parsed is not None:
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
