from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from properties.models import Property
from tenants.models import Tenant
from rentals.models import RentalAgreement, RentCharge
from payments.models import Payment
import datetime


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password123', is_staff=True)
        self.client = Client()

    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_authenticated_user_accesses_dashboard(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Overview Dashboard")

    def test_dashboard_statistics_calculation(self):
        self.client.login(username='testuser', password='password123')

        # Create 1 available property, 1 rented property
        prop_avail = Property.objects.create(
            name="Avail House", property_type=Property.TYPE_HOUSE,
            address="1", city="Hargeisa", monthly_rent=Decimal('100.00'),
            status=Property.STATUS_AVAILABLE
        )
        prop_rented = Property.objects.create(
            name="Rented House", property_type=Property.TYPE_HOUSE,
            address="2", city="Hargeisa", monthly_rent=Decimal('200.00'),
            status=Property.STATUS_AVAILABLE
        )
        tenant = Tenant.objects.create(full_name="Tenant One", phone="123")
        agreement = RentalAgreement.objects.create(
            property=prop_rented, tenant=tenant, monthly_rent=Decimal('200.00'),
            start_date=datetime.date(2026, 11, 1), status=RentalAgreement.STATUS_ACTIVE
        )
        charge = RentCharge.objects.create(
            rental=agreement, billing_month=datetime.date(2026, 11, 1),
            amount_due=Decimal('200.00'), due_date=datetime.date(2026, 11, 5)
        )
        Payment.objects.create(
            rental=agreement, rent_charge=charge, amount=Decimal('150.00'),
            payment_method=Payment.METHOD_CASH, payment_date=datetime.date(2026, 11, 5)
        )

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # Total properties: 2
        self.assertEqual(response.context['total_properties'], 2)
        # Available: 1
        self.assertEqual(response.context['available_properties'], 1)
        # Rented: 1
        self.assertEqual(response.context['rented_properties'], 1)
        # Total tenants: 1
        self.assertEqual(response.context['total_tenants'], 1)
        # Active rentals: 1
        self.assertEqual(response.context['active_rentals'], 1)
        # Total rent collected: 150.00
        self.assertEqual(response.context['total_rent_collected'], Decimal('150.00'))
        # Pending rent balance: 50.00
        self.assertEqual(response.context['pending_rent_balance'], Decimal('50.00'))
