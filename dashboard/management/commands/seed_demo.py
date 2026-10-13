import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction
from properties.models import Property
from tenants.models import Tenant
from rentals.models import RentalAgreement, RentCharge
from payments.models import Payment


class Command(BaseCommand):
    help = "Seed initial demonstration data for Rent House Management System (RHMS)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding RHMS demonstration data...")

        with transaction.atomic():
            # 1. Create User Roles & Default Accounts
            admin_group, _ = Group.objects.get_or_create(name='Admin')
            staff_group, _ = Group.objects.get_or_create(name='Staff')

            # Create Superuser Admin
            admin_user, created = User.objects.get_or_create(
                username='admin',
                defaults={'email': 'admin@rhms.local', 'first_name': 'System', 'last_name': 'Admin'}
            )
            admin_user.set_password('admin123')
            admin_user.is_superuser = True
            admin_user.is_staff = True
            admin_user.save()
            admin_user.groups.add(admin_group)

            # Create Staff User
            staff_user, created = User.objects.get_or_create(
                username='staff',
                defaults={'email': 'staff@rhms.local', 'first_name': 'Reception', 'last_name': 'Staff'}
            )
            staff_user.set_password('staff123')
            staff_user.is_staff = True
            staff_user.is_superuser = False
            staff_user.save()
            staff_user.groups.add(staff_group)

            self.stdout.write(self.style.SUCCESS("Created demo users: admin (admin123) and staff (staff123)"))

            # 2. Create Properties
            prop1, _ = Property.objects.get_or_create(
                name="Ahmed Rental House",
                defaults={
                    'property_type': Property.TYPE_HOUSE,
                    'address': "New Hargeisa",
                    'city': "Hargeisa",
                    'monthly_rent': Decimal('150.00'),
                    'bedrooms': 3,
                    'bathrooms': 2,
                    'description': "Spacious family house with private compound and secure parking.",
                    'status': Property.STATUS_AVAILABLE,
                }
            )

            prop2, _ = Property.objects.get_or_create(
                name="HP Family Apartment",
                defaults={
                    'property_type': Property.TYPE_APARTMENT,
                    'address': "Jigjiga Yar",
                    'city': "Hargeisa",
                    'monthly_rent': Decimal('200.00'),
                    'bedrooms': 2,
                    'bathrooms': 1,
                    'description': "Modern 2-bedroom second-floor apartment close to commercial amenities.",
                    'status': Property.STATUS_AVAILABLE,
                }
            )

            prop3, _ = Property.objects.get_or_create(
                name="Abdi Single Room",
                defaults={
                    'property_type': Property.TYPE_ROOM,
                    'address': "26 June District",
                    'city': "Hargeisa",
                    'monthly_rent': Decimal('75.00'),
                    'bedrooms': 1,
                    'bathrooms': 1,
                    'description': "Clean self-contained single room ideal for a university student or professional.",
                    'status': Property.STATUS_AVAILABLE,
                }
            )

            prop4, _ = Property.objects.get_or_create(
                name="Sea View Villa",
                defaults={
                    'property_type': Property.TYPE_HOUSE,
                    'address': "Coastal Highway",
                    'city': "Berbera",
                    'monthly_rent': Decimal('350.00'),
                    'bedrooms': 4,
                    'bathrooms': 3,
                    'description': "Prime beachside rental villa with garden and ocean breeze.",
                    'status': Property.STATUS_AVAILABLE,
                }
            )

            self.stdout.write(self.style.SUCCESS("Created 4 sample properties."))

            # 3. Create Tenants
            tenant1, _ = Tenant.objects.get_or_create(
                full_name="Ahmed Ali",
                defaults={
                    'phone': "634411223",
                    'email': "ahmed.ali@example.com",
                    'address': "New Hargeisa, Hargeisa",
                    'identification_number': "ID-90812-SOM",
                }
            )

            tenant2, _ = Tenant.objects.get_or_create(
                full_name="Mohamed Hassan",
                defaults={
                    'phone': "634422334",
                    'email': "mohamed.h@example.com",
                    'address': "Jigjiga Yar, Hargeisa",
                    'identification_number': "ID-44219-SOM",
                }
            )

            tenant3, _ = Tenant.objects.get_or_create(
                full_name="Abdi Yusuf",
                defaults={
                    'phone': "634433445",
                    'email': "abdi.yusuf@example.com",
                    'address': "26 June, Hargeisa",
                    'identification_number': "ID-77123-SOM",
                }
            )

            tenant4, _ = Tenant.objects.get_or_create(
                full_name="Fatima Omar",
                defaults={
                    'phone': "634455667",
                    'email': "fatima.omar@example.com",
                    'address': "Daami, Hargeisa",
                    'identification_number': "ID-11029-SOM",
                }
            )

            self.stdout.write(self.style.SUCCESS("Created 4 sample tenants."))

            # 4. Create Rental Agreements
            # Today's reference dates
            today = datetime.date.today()
            nov_billing = datetime.date(today.year, 11, 1) if today.month <= 11 else datetime.date(today.year - 1, 11, 1)
            start_date = datetime.date(nov_billing.year, 11, 1)
            end_date = datetime.date(nov_billing.year + 1, 10, 31)

            # Rental 1 (Active)
            rent1 = RentalAgreement.objects.filter(property=prop1, tenant=tenant1).first()
            if not rent1:
                rent1 = RentalAgreement.objects.create(
                    property=prop1,
                    tenant=tenant1,
                    monthly_rent=prop1.monthly_rent,
                    start_date=start_date,
                    end_date=end_date,
                    security_deposit=Decimal('150.00'),
                    status=RentalAgreement.STATUS_ACTIVE,
                    notes="1-year residential lease. Utilities not included in base rent."
                )

            # Rental 2 (Active)
            rent2 = RentalAgreement.objects.filter(property=prop2, tenant=tenant2).first()
            if not rent2:
                rent2 = RentalAgreement.objects.create(
                    property=prop2,
                    tenant=tenant2,
                    monthly_rent=prop2.monthly_rent,
                    start_date=start_date,
                    end_date=end_date,
                    security_deposit=Decimal('200.00'),
                    status=RentalAgreement.STATUS_ACTIVE,
                    notes="Apartment rented unfurnished. Rent payable on 1st of each month."
                )

            # Rental 3 (Active)
            rent3 = RentalAgreement.objects.filter(property=prop3, tenant=tenant3).first()
            if not rent3:
                rent3 = RentalAgreement.objects.create(
                    property=prop3,
                    tenant=tenant3,
                    monthly_rent=prop3.monthly_rent,
                    start_date=start_date,
                    end_date=end_date,
                    security_deposit=Decimal('75.00'),
                    status=RentalAgreement.STATUS_ACTIVE,
                    notes="Single student room occupancy."
                )

            self.stdout.write(self.style.SUCCESS("Created 3 active rental agreements."))

            # 5. Create Monthly Rent Charges
            charge1, _ = RentCharge.objects.get_or_create(
                rental=rent1,
                billing_month=nov_billing,
                defaults={
                    'amount_due': Decimal('150.00'),
                    'due_date': nov_billing + datetime.timedelta(days=4),
                }
            )

            charge2, _ = RentCharge.objects.get_or_create(
                rental=rent2,
                billing_month=nov_billing,
                defaults={
                    'amount_due': Decimal('200.00'),
                    'due_date': nov_billing + datetime.timedelta(days=4),
                }
            )

            charge3, _ = RentCharge.objects.get_or_create(
                rental=rent3,
                billing_month=nov_billing,
                defaults={
                    'amount_due': Decimal('75.00'),
                    'due_date': nov_billing + datetime.timedelta(days=4),
                }
            )

            self.stdout.write(self.style.SUCCESS("Created 3 monthly rent charges for November."))

            # 6. Create Payments
            # Payment 1: Full $150 via Cash for rent1 -> Paid ($0 balance)
            if not Payment.objects.filter(rent_charge=charge1).exists():
                Payment.objects.create(
                    rental=rent1,
                    rent_charge=charge1,
                    amount=Decimal('150.00'),
                    payment_method=Payment.METHOD_CASH,
                    payment_date=charge1.due_date,
                    reference="CSH-0981",
                    notes="Received full monthly rent in cash at rental office."
                )

            # Payment 2: Partial $100 via ZAAD for rent2 -> Partially Paid ($100 balance)
            if not Payment.objects.filter(rent_charge=charge2).exists():
                Payment.objects.create(
                    rental=rent2,
                    rent_charge=charge2,
                    amount=Decimal('100.00'),
                    payment_method=Payment.METHOD_ZAAD,
                    payment_date=charge2.due_date,
                    reference="ZAAD-TX-883719",
                    notes="Partial payment. Tenant promised remaining $100 balance next week."
                )

            # Payment 3: Full $75 via eDahab for rent3 -> Paid ($0 balance)
            if not Payment.objects.filter(rent_charge=charge3).exists():
                Payment.objects.create(
                    rental=rent3,
                    rent_charge=charge3,
                    amount=Decimal('75.00'),
                    payment_method=Payment.METHOD_EDAHAB,
                    payment_date=charge3.due_date,
                    reference="ED-99210",
                    notes="Full monthly payment sent through eDahab."
                )

            self.stdout.write(self.style.SUCCESS("Created 3 demonstration payments (Cash, ZAAD, eDahab)."))

        self.stdout.write(self.style.SUCCESS("Demonstration seed complete!"))
