import datetime

from django.core import mail
from django.db.utils import IntegrityError
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from utils import referencenumber

from . import models


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

    def test_get_users(self):
        """
        get users
        """
        url = reverse('customuser-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
