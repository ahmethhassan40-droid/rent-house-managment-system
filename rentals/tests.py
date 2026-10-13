import datetime
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from properties.models import Property
from tenants.models import Tenant
from .models import RentalAgreement, RentCharge


class RentalAgreementTests(TestCase):
    def setUp(self):
        self.prop = Property.objects.create(
            name="Alpha House",
            property_type=Property.TYPE_HOUSE,
            address="100 Main St",
            city="Hargeisa",
            monthly_rent=Decimal('150.00'),
            status=Property.STATUS_AVAILABLE
        )
        self.tenant = Tenant.objects.create(
            full_name="Abdi Yusuf",
            phone="634455667"
        )

    def test_agreement_creation_and_number_generation(self):
        agreement = RentalAgreement.objects.create(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date(2026, 11, 1),
            end_date=datetime.date(2027, 10, 31),
            status=RentalAgreement.STATUS_ACTIVE
        )
        self.assertTrue(agreement.rental_number.startswith("RENT-"))
        self.prop.refresh_from_db()
        self.assertEqual(self.prop.status, Property.STATUS_RENTED)

    def test_cannot_have_two_active_agreements_on_same_property(self):
        RentalAgreement.objects.create(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date(2026, 11, 1),
            status=RentalAgreement.STATUS_ACTIVE
        )

        tenant2 = Tenant.objects.create(full_name="Second Tenant", phone="998877")
        second_agreement = RentalAgreement(
            property=self.prop,
            tenant=tenant2,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date(2026, 11, 1),
            status=RentalAgreement.STATUS_ACTIVE
        )
        with self.assertRaises(ValidationError):
            second_agreement.full_clean()

    def test_completing_rental_makes_property_available(self):
        agreement = RentalAgreement.objects.create(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date(2026, 11, 1),
            status=RentalAgreement.STATUS_ACTIVE
        )
        self.prop.refresh_from_db()
        self.assertEqual(self.prop.status, Property.STATUS_RENTED)

        agreement.status = RentalAgreement.STATUS_COMPLETED
        agreement.save()
        self.prop.refresh_from_db()
        self.assertEqual(self.prop.status, Property.STATUS_AVAILABLE)

    def test_invalid_dates_rejected(self):
        agreement = RentalAgreement(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date(2026, 11, 1),
            end_date=datetime.date(2026, 10, 1),  # earlier than start date
            status=RentalAgreement.STATUS_ACTIVE
        )
        with self.assertRaises(ValidationError):
            agreement.full_clean()


class RentChargeTests(TestCase):
    def setUp(self):
        self.prop = Property.objects.create(
            name="Beta House",
            property_type=Property.TYPE_HOUSE,
            address="200 Main St",
            city="Hargeisa",
            monthly_rent=Decimal('150.00'),
            status=Property.STATUS_AVAILABLE
        )
        self.tenant = Tenant.objects.create(full_name="Beta Tenant", phone="123123")
        self.agreement = RentalAgreement.objects.create(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date(2026, 11, 1),
            end_date=datetime.date(2027, 10, 31),
            status=RentalAgreement.STATUS_ACTIVE
        )

    def test_charge_creation_and_balance(self):
        charge = RentCharge.objects.create(
            rental=self.agreement,
            billing_month=datetime.date(2026, 11, 1),
            amount_due=Decimal('150.00'),
            due_date=datetime.date(2026, 11, 5)
        )
        self.assertEqual(charge.total_paid, Decimal('0.00'))
        self.assertEqual(charge.outstanding_balance, Decimal('150.00'))
        self.assertEqual(charge.payment_status, 'Unpaid')

    def test_duplicate_charge_for_same_month_rejected(self):
        RentCharge.objects.create(
            rental=self.agreement,
            billing_month=datetime.date(2026, 11, 1),
            amount_due=Decimal('150.00'),
            due_date=datetime.date(2026, 11, 5)
        )
        duplicate = RentCharge(
            rental=self.agreement,
            billing_month=datetime.date(2026, 11, 1),
            amount_due=Decimal('150.00'),
            due_date=datetime.date(2026, 11, 5)
        )
        with self.assertRaises(Exception):  # Unique constraint or ValidationError
            duplicate.save()
