from twilio.rest import Client

from .models import SMSLog
from .sms import SMSBase


class SMSTwilio(SMSBase):
    """
    Simple wrapper around twilio rest api
    """

    def initialize(self, **kwargs):
        """
        Initialize the twilio client
        """
        self.sid = kwargs["sid"]
        self.token = kwargs["token"]
        self.from_number = kwargs["from_number"]
        self.client = Client(self.sid, self.token)

    def send_sms(self, to_number, message, *argv, **kwargs):
        """
        Send message to a number
        """

        # first log our message
        logentry = SMSLog(
            from_number=self.from_number,
            to_number=to_number,
            message=message,
            via="Twilio",
        )
        logentry.save()

        msg = self.client.messages.create(
            body=message, from_=self.from_number, to=to_number
        )

        logentry.sid = msg.sid
        logentry.save()

        return msg.sid
