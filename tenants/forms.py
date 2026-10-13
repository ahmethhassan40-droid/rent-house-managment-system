from django import forms
from .models import Tenant


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            'full_name',
            'phone',
            'email',
            'address',
            'identification_number',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Ahmed Ali'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 634455667'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ahmed@example.com'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hargeisa'}),
            'identification_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'National ID / Passport No.'}),
        }

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '').strip()
        if not name:
            raise forms.ValidationError("Full name is required.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            raise forms.ValidationError("Phone number is required.")
        return phone
