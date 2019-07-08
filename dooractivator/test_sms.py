import os
import unittest
import datetime

from .sms_twilio import SMSTwilio

envcheck = unittest.skipUnless(
    os.environ.get('TWILIO_SID', False) and
    os.environ.get('TWILIO_TOKEN', False) and
    os.environ.get('TWILIO_FROM', False) and
    os.environ.get('TWILIO_TO', False), 'TWILIO_* Environment variables not set, skipping twilio sms sending test'
)

@envcheck
class TestSMS(unittest.TestCase):
    def test_sendmessage(self):
        """
        Requires env variables

        TWILIO_SID
        TWILIO_TOKEN
        TWILIO_FROM
        TWILIO_TO

        to run
        """
        twilio = SMSTwilio()
        twilio.initialize(
            sid=os.environ['TWILIO_SID'],
            token=os.environ['TWILIO_TOKEN'],
            fromnumber=os.environ['TWILIO_FROM'],
        )

        msg = "twilio test message sent {}".format(datetime.datetime.now().isoformat())
        msgid = twilio.sendsms(twilio.toe164(os.environ['TWILIO_TO']), msg)
        self.assertTrue(msgid)
