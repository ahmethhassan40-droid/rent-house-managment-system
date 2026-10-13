from django.db import models
from django.core.exceptions import ValidationError
from rent_house.utils import generate_unique_code


class Tenant(models.Model):
    tenant_number = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    identification_number = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.tenant_number} - {self.full_name} ({self.phone})"

    def clean(self):
        super().clean()
        if not self.full_name or not self.full_name.strip():
            raise ValidationError({'full_name': 'Tenant full name is required.'})
        if not self.phone or not self.phone.strip():
            raise ValidationError({'phone': 'Tenant phone number is required.'})

    def save(self, *args, **kwargs):
        if not self.tenant_number:
            self.tenant_number = generate_unique_code('TEN', Tenant, 'tenant_number')
        self.full_clean()
        super().save(*args, **kwargs)

    def has_active_rentals(self):
        return self.rentals.filter(status='Active').exists()

    @property
    def active_rentals(self):
        return self.rentals.filter(status='Active')
