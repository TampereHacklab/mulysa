import logging
import re

logger = logging.getLogger(__name__)


class SMSBase:
    country_to_prefix = {
        'fi': '358',
        'se': '46',
        # TODO: complete me
    }

    def toe164(self, number, country='fi'):
        """
        Convert phonenumber to E.164 format. If country is not gived defaults to finland (+358)
        """
        logger.debug('Converting number {number} to E.164 for country {country}'.format(number=number, country=country))

        # already starts with +, probably in correct format already just return it
        if number.startswith('+'):
            return number

        # strip out everything but digits from the number
        re.sub('[^0-9]', '', number)

        # strip out the first number (usually zero)
        number = number[1:]

        # and prepend + and the country number
        prefix = SMSBase.country_to_prefix[country]
        formatted = '+{prefix}{number}'.format(prefix=prefix, number=number)

        logger.debug('Number converted to {}'.format(formatted))

        return formatted

    def initialize(self, **kwargs):
        """
        Implement in subclass. Initialize whatever you need to
        """
        raise NotImplementedError('Subclasses should implement this!')

    def sendsms(self, fromnumber, tonumber, message, *argv, **kwargs):
        """
        Implement in subclass. Send sms message. Should return something for the caller to check that it was ok
        """
        raise NotImplementedError('Subclasses should implement this!')
