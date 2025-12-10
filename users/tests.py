from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

class GoogleLoginCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('google_login')

    def test_missing_role_and_token(self):
        """
        Ensure that we return a 400 error if neither role nor access_token is provided.
        """
        data = {}  # Empty payload
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Please sign in first.')
