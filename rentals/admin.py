from django.contrib import admin
from .models import RentalAgreement, RentCharge


@admin.register(RentalAgreement)
class RentalAgreementAdmin(admin.ModelAdmin):
    list_display = ('rental_number', 'property', 'tenant', 'monthly_rent', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('status', 'start_date')
    search_fields = ('rental_number', 'property__name', 'tenant__full_name', 'tenant__phone')
    readonly_fields = ('rental_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(RentCharge)
class RentChargeAdmin(admin.ModelAdmin):
    list_display = ('rental', 'billing_month', 'amount_due', 'due_date', 'created_at')
    list_filter = ('billing_month', 'due_date')
    search_fields = ('rental__rental_number', 'rental__tenant__full_name')
    readonly_fields = ('created_at',)
    ordering = ('-billing_month',)
