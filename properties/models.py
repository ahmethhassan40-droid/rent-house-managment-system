from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from rent_house.utils import generate_unique_code


class Property(models.Model):
    TYPE_HOUSE = 'House'
    TYPE_ROOM = 'Room'
    TYPE_APARTMENT = 'Apartment'

    PROPERTY_TYPES = [
        (TYPE_HOUSE, 'House'),
        (TYPE_ROOM, 'Room'),
        (TYPE_APARTMENT, 'Apartment'),
    ]

    STATUS_AVAILABLE = 'Available'
    STATUS_RENTED = 'Rented'
    STATUS_MAINTENANCE = 'Maintenance'
    STATUS_INACTIVE = 'Inactive'

    STATUS_CHOICES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_RENTED, 'Rented'),
        (STATUS_MAINTENANCE, 'Maintenance'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    property_code = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=150)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2)
    bedrooms = models.PositiveIntegerField(null=True, blank=True, default=0)
    bathrooms = models.PositiveIntegerField(null=True, blank=True, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Properties'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.property_code} - {self.name} ({self.city})"

    def clean(self):
        super().clean()
        if self.monthly_rent is not None and self.monthly_rent <= Decimal('0.00'):
            raise ValidationError({'monthly_rent': 'Monthly rent must be greater than zero.'})

        # Do not allow property to be marked Available if an active rental agreement exists
        if self.pk and self.status == self.STATUS_AVAILABLE:
            if self.rentals.filter(status='Active').exists():
                raise ValidationError({
                    'status': 'This property has an active rental agreement and cannot be marked Available.'
                })

    def save(self, *args, **kwargs):
        if not self.property_code:
            self.property_code = generate_unique_code('PROP', Property, 'property_code')
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def active_rental(self):
        """Return the current active rental agreement if one exists."""
        return self.rentals.filter(status='Active').first()

    def has_active_rental(self):
        return self.rentals.filter(status='Active').exists()
