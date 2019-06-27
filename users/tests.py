import datetime
import time

from django.core import mail
from django.db.utils import IntegrityError
from django.dispatch import receiver
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from utils import referencenumber

from . import models, signals


class UserManagerTests(APITestCase):
    def test_create_superuser(self):
        models.CustomUser.objects.create_superuser(email='testsuper@example.com',
                                                   first_name='test',
                                                   last_name='super',
                                                   phone='123123',
                                                   password='abc123')
        self.assertIsNotNone(models.CustomUser.objects.get(email='testsuper@example.com'))

class UsersTests(APITestCase):
    def test_create_user_invalid(self):
        # note, if your test generates exceptions it will brake the transaction
        # https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom
        u = models.CustomUser()
        # cannot save without data
        with self.assertRaises(IntegrityError):
            u.save()

    def test_create_user(self):
        """
        Basic model testing
        """
        u = models.CustomUser()
        u.email = 'test@example.com'
        u.birthday = datetime.datetime.now()
        u.save()

        # check that we got a reference number automatically and it matches
        ref = referencenumber.generate(u.id*100)
        self.assertEqual(u.reference_number, ref, 'auto generated reference number matches')

        # check the the welcome email was sent and contains the reference number
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(str(ref), mail.outbox[0].body, 'reference number found in welcome email')

        # for completenes sake
        self.assertEqual(u.email, u.get_short_name())
        self.assertEqual(u.email, u.natural_key())

    def test_signals(self):
        u = models.CustomUser()
        u.email = 'signaltest@example.com'
        u.birthday = datetime.datetime.now()
        u.save()

        self.activate_call_counter = 0
        self.activate_instance_id = None

        self.deactivate_call_counter = 0
        self.deactivate_instance_id = None

        self.assertTrue(u.is_active, 'user is active')

        # dummy listeners
        @receiver(signals.deactivate_user, sender=models.CustomUser)
        def dummy_activate_listener(sender, instance: models.CustomUser, **kwargs):
            self.activate_instance_id = instance.id
            self.activate_call_counter += 1

        @receiver(signals.deactivate_user, sender=models.CustomUser)
        def dummy_deactivate_listener(sender, instance: models.CustomUser, **kwargs):
            self.deactivate_instance_id = instance.id
            self.deactivate_call_counter += 1

        # deactivation triggers signal
        u.is_active = False
        u.save()

        time.sleep(1)

        # user activation triggers signal
        u.is_active = True
        u.save()

        time.sleep(1)

        # and check that our receivers were called
        self.assertEqual(self.activate_call_counter, 1, 'activate signal was called once')
        self.assertEqual(self.deactivate_call_counter, 1, 'deactivate signal was called once')
        self.assertEqual(u.id, self.activate_instance_id, 'signal instance id matches')
        self.assertEqual(u.id, self.deactivate_instance_id, 'signal instance id matches')

class UsersAPITests(APITestCase):
    def test_get_users(self):
        """
        get users api call
        """
        url = reverse('customuser-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
