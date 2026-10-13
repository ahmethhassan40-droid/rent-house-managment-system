from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'rental', 'rent_charge', 'amount', 'payment_method', 'payment_date', 'created_at')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('payment_number', 'rental__rental_number', 'rental__tenant__full_name', 'reference')
    readonly_fields = ('payment_number', 'created_at')
    date_hierarchy = 'payment_date'
    ordering = ('-payment_date', '-created_at')
