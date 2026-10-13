from decimal import Decimal
from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum
from rentals.models import RentalAgreement, RentCharge
from rent_house.utils import generate_unique_code


class Payment(models.Model):
    METHOD_CASH = 'Cash'
    METHOD_ZAAD = 'ZAAD'
    METHOD_EDAHAB = 'eDahab'
    METHOD_CARD = 'Card'
    METHOD_BANK = 'Bank'

    PAYMENT_METHODS = [
        (METHOD_CASH, 'Cash'),
        (METHOD_ZAAD, 'ZAAD'),
        (METHOD_EDAHAB, 'eDahab'),
        (METHOD_CARD, 'Card'),
        (METHOD_BANK, 'Bank'),
    ]

    payment_number = models.CharField(max_length=20, unique=True, editable=False)
    rental = models.ForeignKey(RentalAgreement, on_delete=models.PROTECT, related_name='payments')
    rent_charge = models.ForeignKey(RentCharge, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_date = models.DateField(default=timezone.now)
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.payment_number} - {self.rental.rental_number} (${self.amount})"

    def clean(self):
        super().clean()
        if self.amount is not None and self.amount <= Decimal('0.00'):
            raise ValidationError({'amount': 'Payment amount must be greater than zero.'})

        if self.rent_charge_id and self.rental_id:
            # Payment and rent charge must belong to the same rental agreement
            if self.rent_charge.rental_id != self.rental_id:
                raise ValidationError({
                    'rent_charge': 'The selected rent charge does not belong to this rental agreement.'
                })

            # Check remaining balance for charge to prevent overpayment
            payments_query = self.rent_charge.payments.all()
            if self.pk:
                payments_query = payments_query.exclude(pk=self.pk)

            existing_paid = payments_query.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            remaining_balance = self.rent_charge.amount_due - existing_paid

            if self.amount is not None and self.amount > remaining_balance:
                raise ValidationError({
                    'amount': f"Payment amount (${self.amount}) exceeds the remaining balance (${remaining_balance}) for this charge."
                })

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.payment_number:
                self.payment_number = generate_unique_code('PAY', Payment, 'payment_number')
            # If rent_charge is provided but rental is not, link automatically
            if self.rent_charge_id and not self.rental_id:
                self.rental = self.rent_charge.rental
            self.full_clean()
            super().save(*args, **kwargs)
