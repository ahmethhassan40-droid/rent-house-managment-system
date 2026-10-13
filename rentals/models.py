import datetime
import builtins
from decimal import Decimal
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.db.models import Sum
from properties.models import Property
from tenants.models import Tenant
from rent_house.utils import generate_unique_code


class RentalAgreement(models.Model):
    STATUS_ACTIVE = 'Active'
    STATUS_COMPLETED = 'Completed'
    STATUS_CANCELLED = 'Cancelled'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    rental_number = models.CharField(max_length=20, unique=True, editable=False)
    property = models.ForeignKey(Property, on_delete=models.PROTECT, related_name='rentals')
    tenant = models.ForeignKey(Tenant, on_delete=models.PROTECT, related_name='rentals')
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.rental_number} - {self.property.name} ({self.tenant.full_name})"

    def clean(self):
        super().clean()
        if self.monthly_rent is not None and self.monthly_rent <= Decimal('0.00'):
            raise ValidationError({'monthly_rent': 'Monthly rent must be greater than zero.'})

        if self.security_deposit is not None and self.security_deposit < Decimal('0.00'):
            raise ValidationError({'security_deposit': 'Security deposit cannot be negative.'})

        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError({'end_date': 'End date cannot be earlier than start date.'})

        # Property availability validation for Active rental
        if self.property_id and self.status == self.STATUS_ACTIVE:
            conflicting_active = RentalAgreement.objects.filter(
                property=self.property,
                status=self.STATUS_ACTIVE
            )
            if self.pk:
                conflicting_active = conflicting_active.exclude(pk=self.pk)

            if conflicting_active.exists():
                raise ValidationError({
                    'property': f"Property '{self.property.name}' already has an active rental agreement ({conflicting_active.first().rental_number})."
                })

            # Check that property is available if this is a newly assigned agreement
            if not self.pk:
                if self.property.status != Property.STATUS_AVAILABLE:
                    raise ValidationError({
                        'property': f"Property '{self.property.name}' is currently {self.property.status}. Only Available properties can be rented."
                    })

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.rental_number:
                self.rental_number = generate_unique_code('RENT', RentalAgreement, 'rental_number')

            self.full_clean()
            super().save(*args, **kwargs)

            # Update property status accordingly
            prop = self.property
            if self.status == self.STATUS_ACTIVE:
                if prop.status != Property.STATUS_RENTED:
                    prop.status = Property.STATUS_RENTED
                    prop.save(update_fields=['status', 'updated_at'])
            elif self.status in [self.STATUS_COMPLETED, self.STATUS_CANCELLED]:
                # If there are no other active rentals for this property and not Maintenance, mark Available
                has_other_active = RentalAgreement.objects.filter(
                    property=prop,
                    status=self.STATUS_ACTIVE
                ).exclude(pk=self.pk).exists()

                if not has_other_active and prop.status != Property.STATUS_MAINTENANCE:
                    prop.status = Property.STATUS_AVAILABLE
                    prop.save(update_fields=['status', 'updated_at'])

    @builtins.property
    def total_charges(self) -> Decimal:
        """Sum of all generated rent charges."""
        val = self.charges.aggregate(total=Sum('amount_due'))['total']
        return val if val is not None else Decimal('0.00')

    @builtins.property
    def total_payments(self) -> Decimal:
        """Sum of all payments made towards charges on this rental."""
        val = self.payments.aggregate(total=Sum('amount'))['total']
        return val if val is not None else Decimal('0.00')

    @builtins.property
    def outstanding_balance(self) -> Decimal:
        """Difference between total recorded charges and payments."""
        return self.total_charges - self.total_payments

    @builtins.property
    def has_charges(self) -> bool:
        return self.charges.exists()



class RentCharge(models.Model):
    rental = models.ForeignKey(RentalAgreement, on_delete=models.PROTECT, related_name='charges')
    billing_month = models.DateField(help_text="First day of billing month (e.g., 2026-11-01)")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-billing_month']
        constraints = [
            models.UniqueConstraint(
                fields=['rental', 'billing_month'],
                name='unique_rental_billing_month'
            )
        ]

    def __str__(self):
        month_str = self.billing_month.strftime('%B %Y') if self.billing_month else ''
        return f"{self.rental.rental_number} - {month_str} (${self.amount_due})"

    def clean(self):
        super().clean()
        if self.amount_due is not None and self.amount_due <= Decimal('0.00'):
            raise ValidationError({'amount_due': 'Amount due must be greater than zero.'})

        if self.billing_month:
            # Ensure billing_month is normalized to the 1st of the month
            self.billing_month = datetime.date(self.billing_month.year, self.billing_month.month, 1)

            # Validate that billing_month is within the rental agreement's valid period
            if self.rental_id:
                rental_start_first = datetime.date(self.rental.start_date.year, self.rental.start_date.month, 1)
                if self.billing_month < rental_start_first:
                    raise ValidationError({
                        'billing_month': f"Billing month cannot precede the rental agreement start month ({rental_start_first.strftime('%B %Y')})."
                    })

                if self.rental.end_date:
                    rental_end_first = datetime.date(self.rental.end_date.year, self.rental.end_date.month, 1)
                    if self.billing_month > rental_end_first:
                        raise ValidationError({
                            'billing_month': f"Billing month cannot be after the rental agreement end month ({rental_end_first.strftime('%B %Y')})."
                        })

    def save(self, *args, **kwargs):
        if self.billing_month:
            self.billing_month = datetime.date(self.billing_month.year, self.billing_month.month, 1)
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_paid(self) -> Decimal:
        """Sum of all payments for this charge."""
        val = self.payments.aggregate(total=Sum('amount'))['total']
        return val if val is not None else Decimal('0.00')

    @property
    def outstanding_balance(self) -> Decimal:
        """Remaining balance on this charge."""
        return max(Decimal('0.00'), self.amount_due - self.total_paid)

    @property
    def payment_status(self) -> str:
        """Status display: Paid, Partially Paid, Unpaid."""
        paid = self.total_paid
        if paid >= self.amount_due:
            return 'Paid'
        elif paid > Decimal('0.00'):
            return 'Partially Paid'
        else:
            return 'Unpaid'
