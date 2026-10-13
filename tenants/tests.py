from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Tenant


class TenantModelTests(TestCase):
    def test_tenant_creation_and_number_generation(self):
        tenant = Tenant.objects.create(
            full_name="Ahmed Ali",
            phone="634411223",
            email="ahmed@example.com"
        )
        self.assertIsNotNone(tenant.tenant_number)
        self.assertTrue(tenant.tenant_number.startswith("TEN-"))

    def test_tenant_name_and_phone_required(self):
        tenant = Tenant(full_name="", phone="")
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    def test_tenant_search(self):
        user = User.objects.create_user('staff', 'staff@test.com', 'password', is_staff=True)
        client = Client()
        client.login(username='staff', password='password')

        Tenant.objects.create(full_name="Unique Search Name", phone="777888999")
        Tenant.objects.create(full_name="Another Person", phone="111222333")

        response = client.get(reverse('tenant_list') + '?q=Unique')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unique Search Name")
        self.assertNotContains(response, "Another Person")
