from decimal import Decimal
from django import forms
from .models import Property


class PropertyForm(forms.ModelForm):
    class Meta:
        model = Property
        fields = [
            'name',
            'property_type',
            'description',
            'address',
            'city',
            'monthly_rent',
            'bedrooms',
            'bathrooms',
            'status',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ahmed Rental House'}),
            'property_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional details about the property...'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. New Hargeisa'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hargeisa'}),
            'monthly_rent': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0.00'}),
            'bedrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'bathrooms': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_monthly_rent(self):
        rent = self.cleaned_data.get('monthly_rent')
        if rent is None or rent <= Decimal('0.00'):
            raise forms.ValidationError("Monthly rent must be greater than zero.")
        return rent
