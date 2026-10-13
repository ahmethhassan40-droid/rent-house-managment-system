from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='johndoe',
            password='secretpassword123'
        )

    def test_login_success_and_redirect_to_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'johndoe',
            'password': 'secretpassword123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('dashboard'), response.url)

    def test_login_invalid_credentials_shows_error(self):
        response = self.client.post(reverse('login'), {
            'username': 'johndoe',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct username and password")

    def test_logout_requires_post(self):
        self.client.login(username='johndoe', password='secretpassword123')
        # Django 5 requires POST for logout
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        # Verify user is logged out
        resp_dashboard = self.client.get(reverse('dashboard'))
        self.assertEqual(resp_dashboard.status_code, 302)
        self.assertIn('/login/', resp_dashboard.url)
