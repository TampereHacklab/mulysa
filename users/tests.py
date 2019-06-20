from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# from . import models


class UsersTests(APITestCase):
    def test_get_users(self):
        """
        get users
        """
        url = reverse('customuser-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
