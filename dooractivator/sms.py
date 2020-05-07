import logging
import re

logger = logging.getLogger(__name__)


class SMSBase:
    country_to_prefix = {
        "fi": "358",
        "se": "46",
        # TODO: complete me
    }

    def toe164(self, number, country="fi"):
        """
        Convert phonenumber to E.164 format. If country is not gived defaults to finland (+358)
        """
        logger.debug(
            "Converting number {number} to E.164 for country {country}".format(
                number=number, country=country
            )
        )

        # already starts with +, probably in correct format already just return it
        if number.startswith("+"):
            return number

        # strip out everything but digits from the number
        re.sub("[^0-9]", "", number)

        # strip out the first number (usually zero)
        number = number[1:]

        # and prepend + and the country number
        prefix = SMSBase.country_to_prefix[country]
        formatted = "+{prefix}{number}".format(prefix=prefix, number=number)

        logger.debug("Number converted to {}".format(formatted))

        return formatted

    def build_activate_access_message(
        self, number, name, gate="B", auth="C", period="L", country="fi", **kwargs
    ):
        """
        Build message for activating door access for a number

        The format is for GSM Gate Control 1000 (thats what we have right now)

        https://github.com/TampereHacklab/GSM-lock-system/blob/master/Gate_Control_1000_v3-13_EN_Manual_12-08-2013.pdf
        """
        msg = "*n={number},{name},{auth},{period},{gate}#".format(
            number=self.toe164(number, country=country),
            name=name,
            gate=gate,
            auth=auth,
            period=period,
        )
        return msg

    def build_deactivate_access_message(self, number, name, country="fi", **kwargs):
        """
        Build message for deactivating door access for a number

        The format is for GSM Gate Control 1000 (thats what we have right now)

        https://github.com/TampereHacklab/GSM-lock-system/blob/master/Gate_Control_1000_v3-13_EN_Manual_12-08-2013.pdf
        """
        msg = "*d={number}#".format(
            number=self.toe164(number, country=country),
        )
        return msg

    def initialize(self, **kwargs):
        """
        Implement in subclass. Initialize whatever you need to
        """
        raise NotImplementedError("Subclasses should implement this!")

    def send_sms(self, fromnumber, tonumber, message, *argv, **kwargs):
        """
        Implement in subclass. Send sms message. Should return something for the caller to check that it was ok
        """
        raise NotImplementedError("Subclasses should implement this!")
