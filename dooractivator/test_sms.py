import datetime
import os
import unittest

from .models import SMSLog
from .sms_twilio import SMSTwilio

envcheck = unittest.skipUnless(os.environ.get('TWILIO_SID', False) and
                               os.environ.get('TWILIO_TOKEN', False) and
                               os.environ.get('TWILIO_FROM', False) and
                               os.environ.get('TWILIO_TO', False),
                               'TWILIO_* Environment variables not set, skipping twilio sms sending test'
                               )

@envcheck
class TestSMS(unittest.TestCase):
    def test_sendmessage(self):
        """
        Requires env variables

        export TWILIO_SID=your_twilio_account_sid
        export TWILIO_TOKEN=your_twilio_account_token
        export TWILIO_FROM=your_twilio_account_from_number
        export TWILIO_TO=your_phone_number

        to run
        """
        twilio = SMSTwilio()
        twilio.initialize(
            sid=os.environ['TWILIO_SID'],
            token=os.environ['TWILIO_TOKEN'],
            from_number=os.environ['TWILIO_FROM'],
        )

        msg = 'twilio test message sent {}'.format(datetime.datetime.now().isoformat())
        msgid = twilio.send_sms(twilio.toe164(os.environ['TWILIO_TO']), msg)
        self.assertTrue(msgid)

        # check that we were logged
        self.assertEqual(SMSLog.objects.filter(sid=msgid).count(), 1)
