from decimal import Decimal
from django import forms
from .models import Payment
from rentals.models import RentalAgreement, RentCharge


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'rental',
            'rent_charge',
            'amount',
            'payment_method',
            'payment_date',
            'reference',
            'notes',
        ]
        widgets = {
            'rental': forms.Select(attrs={'class': 'form-control', 'id': 'id_rental'}),
            'rent_charge': forms.Select(attrs={'class': 'form-control', 'id': 'id_rent_charge'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reference': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mobile Tx ID, Check #, Cash Receipt'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional payment notes...'}),
        }

    def __init__(self, *args, **kwargs):
        rental_initial = kwargs.pop('rental_initial', None)
        charge_initial = kwargs.pop('charge_initial', None)
        super().__init__(*args, **kwargs)

        # Set rental queryset
        self.fields['rental'].queryset = RentalAgreement.objects.select_related('property', 'tenant').order_by('-created_at')

        # Limit charges to relevant rental if initial or bound
        rental_id = None
        if self.is_bound:
            rental_id = self.data.get('rental')
        elif rental_initial:
            rental_id = rental_initial.pk
            self.fields['rental'].initial = rental_initial
        elif self.instance.pk:
            rental_id = self.instance.rental_id

        if rental_id:
            self.fields['rent_charge'].queryset = RentCharge.objects.filter(rental_id=rental_id).order_by('-billing_month')
        else:
            self.fields['rent_charge'].queryset = RentCharge.objects.select_related('rental').order_by('-billing_month')

        if charge_initial:
            self.fields['rent_charge'].initial = charge_initial
            self.fields['amount'].initial = charge_initial.outstanding_balance

    def clean(self):
        cleaned_data = super().clean()
        rental = cleaned_data.get('rental')
        rent_charge = cleaned_data.get('rent_charge')
        amount = cleaned_data.get('amount')

        if amount is not None and amount <= Decimal('0.00'):
            self.add_error('amount', "Payment amount must be greater than zero.")

        if rental and rent_charge:
            if rent_charge.rental_id != rental.pk:
                self.add_error(
                    'rent_charge',
                    f"Selected rent charge does not belong to rental agreement {rental.rental_number}."
                )

            # Prevent payment exceeding the remaining charge balance
            payments_qs = rent_charge.payments.all()
            if self.instance.pk:
                payments_qs = payments_qs.exclude(pk=self.instance.pk)

            from django.db.models import Sum
            already_paid = payments_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            remaining_balance = rent_charge.amount_due - already_paid

            if amount is not None and amount > remaining_balance:
                self.add_error(
                    'amount',
                    f"Payment amount (${amount}) exceeds the remaining balance (${remaining_balance}) for this charge."
                )

        return cleaned_data
