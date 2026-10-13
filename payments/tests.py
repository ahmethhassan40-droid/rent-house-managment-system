import datetime
from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from properties.models import Property
from tenants.models import Tenant
from rentals.models import RentalAgreement, RentCharge
from .models import Payment


class PaymentModelTests(TestCase):
    def setUp(self):
        self.prop = Property.objects.create(
            name="Payment Prop",
            property_type=Property.TYPE_HOUSE,
            address="Payment St",
            city="Hargeisa",
            monthly_rent=Decimal('150.00'),
            status=Property.STATUS_AVAILABLE
        )
        self.tenant = Tenant.objects.create(full_name="Payment Tenant", phone="634499887")
        self.agreement = RentalAgreement.objects.create(
            property=self.prop,
            tenant=self.tenant,
            monthly_rent=Decimal('150.00'),
            start_date=datetime.date(2026, 11, 1),
            status=RentalAgreement.STATUS_ACTIVE
        )
        self.charge = RentCharge.objects.create(
            rental=self.agreement,
            billing_month=datetime.date(2026, 11, 1),
            amount_due=Decimal('150.00'),
            due_date=datetime.date(2026, 11, 5)
        )

    def test_payment_creation_and_balance_calculation(self):
        payment = Payment.objects.create(
            rental=self.agreement,
            rent_charge=self.charge,
            amount=Decimal('100.00'),
            payment_method=Payment.METHOD_ZAAD,
            payment_date=datetime.date(2026, 11, 5)
        )
        self.assertTrue(payment.payment_number.startswith("PAY-"))
        self.assertEqual(self.charge.total_paid, Decimal('100.00'))
        self.assertEqual(self.charge.outstanding_balance, Decimal('50.00'))
        self.assertEqual(self.charge.payment_status, 'Partially Paid')

        # Add remaining 50
        Payment.objects.create(
            rental=self.agreement,
            rent_charge=self.charge,
            amount=Decimal('50.00'),
            payment_method=Payment.METHOD_CASH,
            payment_date=datetime.date(2026, 11, 6)
        )
        self.assertEqual(self.charge.total_paid, Decimal('150.00'))
        self.assertEqual(self.charge.outstanding_balance, Decimal('0.00'))
        self.assertEqual(self.charge.payment_status, 'Paid')

    def test_overpayment_rejected(self):
        overpay = Payment(
            rental=self.agreement,
            rent_charge=self.charge,
            amount=Decimal('200.00'),  # Exceeds 150
            payment_method=Payment.METHOD_CASH
        )
        with self.assertRaises(ValidationError):
            overpay.full_clean()

    def test_payment_charge_mismatch_rejected(self):
        other_prop = Property.objects.create(
            name="Other Prop",
            property_type=Property.TYPE_ROOM,
            address="Other St",
            city="Hargeisa",
            monthly_rent=Decimal('100.00'),
            status=Property.STATUS_AVAILABLE
        )
        other_agreement = RentalAgreement.objects.create(
            property=other_prop,
            tenant=self.tenant,
            monthly_rent=Decimal('100.00'),
            start_date=datetime.date(2026, 11, 1),
            status=RentalAgreement.STATUS_ACTIVE
        )
        # Try to pay for self.charge but assign to other_agreement
        mismatch_payment = Payment(
            rental=other_agreement,
            rent_charge=self.charge,
            amount=Decimal('50.00'),
            payment_method=Payment.METHOD_CASH
        )
        with self.assertRaises(ValidationError):
            mismatch_payment.full_clean()
