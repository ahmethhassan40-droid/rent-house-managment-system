from django.contrib import admin
from .models import Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('property_code', 'name', 'property_type', 'city', 'monthly_rent', 'status', 'created_at')
    list_filter = ('property_type', 'status', 'city')
    search_fields = ('property_code', 'name', 'address', 'city')
    readonly_fields = ('property_code', 'created_at', 'updated_at')
    ordering = ('-created_at',)
