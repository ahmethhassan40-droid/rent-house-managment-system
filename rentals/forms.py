import datetime
from decimal import Decimal
from django import forms
from django.db import models
from .models import RentalAgreement, RentCharge
from properties.models import Property
from tenants.models import Tenant



class RentalAgreementForm(forms.ModelForm):
    class Meta:
        model = RentalAgreement
        fields = [
            'property',
            'tenant',
            'monthly_rent',
            'start_date',
            'end_date',
            'security_deposit',
            'status',
            'notes',
        ]
        widgets = {
            'property': forms.Select(attrs={'class': 'form-control'}),
            'tenant': forms.Select(attrs={'class': 'form-control'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'security_deposit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional agreement terms or notes...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For new agreements, show available properties (or current property if editing)
        if not self.instance.pk:
            self.fields['property'].queryset = Property.objects.filter(status=Property.STATUS_AVAILABLE)
        else:
            self.fields['property'].queryset = Property.objects.filter(
                models.Q(status=Property.STATUS_AVAILABLE) | models.Q(pk=self.instance.property_id)
            )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        monthly_rent = cleaned_data.get('monthly_rent')
        security_deposit = cleaned_data.get('security_deposit')
        prop = cleaned_data.get('property')
        status = cleaned_data.get('status')

        if monthly_rent is not None and monthly_rent <= Decimal('0.00'):
            self.add_error('monthly_rent', "Monthly rent must be greater than zero.")

        if security_deposit is not None and security_deposit < Decimal('0.00'):
            self.add_error('security_deposit', "Security deposit cannot be negative.")

        if start_date and end_date and end_date < start_date:
            self.add_error('end_date', "End date cannot be earlier than start date.")

        if prop and status == RentalAgreement.STATUS_ACTIVE:
            conflicts = RentalAgreement.objects.filter(
                property=prop,
                status=RentalAgreement.STATUS_ACTIVE
            )
            if self.instance.pk:
                conflicts = conflicts.exclude(pk=self.instance.pk)

            if conflicts.exists():
                self.add_error('property', f"Property '{prop.name}' already has an active rental agreement.")

        return cleaned_data


class RentalStatusForm(forms.ModelForm):
    class Meta:
        model = RentalAgreement
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class RentChargeForm(forms.ModelForm):
    billing_month_input = forms.CharField(
        label="Billing Month",
        widget=forms.TextInput(attrs={'class': 'form-control', 'type': 'month', 'placeholder': 'YYYY-MM'}),
        help_text="Select the month and year for this rent charge (e.g. 2026-11)."
    )

    class Meta:
        model = RentCharge
        fields = [
            'rental',
            'amount_due',
            'due_date',
        ]
        widgets = {
            'rental': forms.Select(attrs={'class': 'form-control'}),
            'amount_due': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        rental_initial = kwargs.pop('rental_initial', None)
        super().__init__(*args, **kwargs)

        if rental_initial:
            self.fields['rental'].initial = rental_initial
            self.fields['amount_due'].initial = rental_initial.monthly_rent

        # Limit to active rentals for convenient charge generation
        self.fields['rental'].queryset = RentalAgreement.objects.select_related('property', 'tenant').order_by('-created_at')

        if self.instance.pk and self.instance.billing_month:
            self.fields['billing_month_input'].initial = self.instance.billing_month.strftime('%Y-%m')

    def clean(self):
        cleaned_data = super().clean()
        month_str = cleaned_data.get('billing_month_input')
        rental = cleaned_data.get('rental')
        amount_due = cleaned_data.get('amount_due')

        if amount_due is not None and amount_due <= Decimal('0.00'):
            self.add_error('amount_due', "Amount due must be greater than zero.")

        if month_str:
            try:
                parts = month_str.split('-')
                billing_date = datetime.date(int(parts[0]), int(parts[1]), 1)
                self.instance.billing_month = billing_date
            except (ValueError, IndexError):
                self.add_error('billing_month_input', "Invalid billing month format. Please use YYYY-MM.")
                return cleaned_data

            if rental:
                rental_start_first = datetime.date(rental.start_date.year, rental.start_date.month, 1)
                if billing_date < rental_start_first:
                    self.add_error(
                        'billing_month_input',
                        f"Billing month cannot precede the rental agreement start month ({rental_start_first.strftime('%B %Y')})."
                    )

                if rental.end_date:
                    rental_end_first = datetime.date(rental.end_date.year, rental.end_date.month, 1)
                    if billing_date > rental_end_first:
                        self.add_error(
                            'billing_month_input',
                            f"Billing month cannot be after the rental agreement end month ({rental_end_first.strftime('%B %Y')})."
                        )

                # Check duplicate charge for same rental and billing month
                existing = RentCharge.objects.filter(rental=rental, billing_month=billing_date)
                if self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    self.add_error(
                        'billing_month_input',
                        f"A rent charge already exists for {billing_date.strftime('%B %Y')} on agreement {rental.rental_number}."
                    )

        return cleaned_data
