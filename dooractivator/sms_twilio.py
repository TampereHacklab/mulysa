from twilio.rest import Client

from .sms import SMSBase


class SMSTwilio(SMSBase):
    """
    Simple wrapper around twilio rest api
    """
    def initialize(self, **kwargs):
        """
        Initialize the twilio client
        """
        self.sid = kwargs['sid']
        self.token = kwargs['token']
        self.fromnumber = kwargs['fromnumber']
        self.client = Client(self.sid, self.token)

    def sendsms(self, tonumber, message, *argv, **kwargs):
        """
        Send message to a number
        """
        msg = self.client.messages.create(
            body=message,
            from_=self.fromnumber,
            to=tonumber
        )
        return msg.sid
