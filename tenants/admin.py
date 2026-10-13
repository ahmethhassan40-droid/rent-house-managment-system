from django.contrib import admin
from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('tenant_number', 'full_name', 'phone', 'email', 'created_at')
    search_fields = ('tenant_number', 'full_name', 'phone', 'identification_number')
    readonly_fields = ('tenant_number', 'created_at', 'updated_at')
    ordering = ('-created_at',)
