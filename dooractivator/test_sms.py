import datetime
import os
import unittest

from .models import SMSLog
from .sms import SMSBase
from .sms_twilio import SMSTwilio

# environment checker for some of the tests
envcheck = unittest.skipUnless(os.environ.get('TWILIO_SID', False) and
                               os.environ.get('TWILIO_TOKEN', False) and
                               os.environ.get('TWILIO_FROM', False) and
                               os.environ.get('TWILIO_TO', False),
                               'TWILIO_* Environment variables not set, skipping twilio sms sending test'
                               )

class TestMessage(unittest.TestCase):
    def test_activation_msg(self):
        sms = SMSBase()
        msg = sms.build_activate_access_message(number='1234567890', name='test name')
        self.assertEqual(msg, '*n=+358234567890,test name,C,L,B#')

    def test_deactivation_msg(self):
        sms = SMSBase()
        msg = sms.build_deactivate_access_message(number='1234567890', name='test name')
        self.assertEqual(msg, '*d=+358234567890#')

    def test_e164(self):
        sms = SMSBase()
        num = sms.toe164('1234567890')
        self.assertEqual(num, '+358234567890')


@envcheck
class TestSMS(unittest.TestCase):
    """
    These are only ran if environment variables are ok
    """
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
