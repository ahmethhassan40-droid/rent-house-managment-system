from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Property
from tenants.models import Tenant
from rentals.models import RentalAgreement
import datetime


class PropertyModelTests(TestCase):
    def test_property_creation_and_code_generation(self):
        prop = Property.objects.create(
            name="Test House",
            property_type=Property.TYPE_HOUSE,
            address="123 Street",
            city="Hargeisa",
            monthly_rent=Decimal('150.00'),
            bedrooms=3,
            bathrooms=2,
        )
        self.assertIsNotNone(prop.property_code)
        self.assertTrue(prop.property_code.startswith("PROP-"))
        self.assertEqual(prop.status, Property.STATUS_AVAILABLE)

    def test_monthly_rent_must_be_positive(self):
        prop = Property(
            name="Zero Rent House",
            property_type=Property.TYPE_HOUSE,
            address="123 Street",
            city="Hargeisa",
            monthly_rent=Decimal('0.00')
        )
        with self.assertRaises(ValidationError):
            prop.full_clean()

    def test_cannot_mark_available_when_active_rental_exists(self):
        prop = Property.objects.create(
            name="Active House",
            property_type=Property.TYPE_HOUSE,
            address="123 Street",
            city="Hargeisa",
            monthly_rent=Decimal('150.00')
        )
        tenant = Tenant.objects.create(
            full_name="John Doe",
            phone="123456"
        )
        agreement = RentalAgreement.objects.create(
            property=prop,
            tenant=tenant,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date.today(),
            status=RentalAgreement.STATUS_ACTIVE
        )
        prop.refresh_from_db()
        self.assertEqual(prop.status, Property.STATUS_RENTED)

        # Attempt to change status to Available
        prop.status = Property.STATUS_AVAILABLE
        with self.assertRaises(ValidationError):
            prop.full_clean()

    def test_property_with_active_rental_cannot_be_deleted(self):
        admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'password')
        client = Client()
        client.login(username='admin', password='password')

        prop = Property.objects.create(
            name="Delete Protected House",
            property_type=Property.TYPE_HOUSE,
            address="123 Street",
            city="Hargeisa",
            monthly_rent=Decimal('150.00')
        )
        tenant = Tenant.objects.create(
            full_name="Jane Doe",
            phone="987654"
        )
        RentalAgreement.objects.create(
            property=prop,
            tenant=tenant,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date.today(),
            status=RentalAgreement.STATUS_ACTIVE
        )

        response = client.post(reverse('property_delete', args=[prop.pk]))
        # Should redirect back to detail and property still exists
        self.assertTrue(Property.objects.filter(pk=prop.pk).exists())
