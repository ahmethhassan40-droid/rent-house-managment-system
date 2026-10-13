"""
Main URL configuration for Rent House Management System (RHMS).
"""

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


def root_redirect(request):
    """Redirect root path to dashboard (or login for unauthenticated users)."""
    return redirect('dashboard')


urlpatterns = [
    # Administration
    path('admin/', admin.site.urls),

    # Authentication
    path('', include('accounts.urls')),

    # Root redirect
    path('', root_redirect, name='root'),

    # Application Modules
    path('dashboard/', include('dashboard.urls')),
    path('properties/', include('properties.urls')),
    path('tenants/', include('tenants.urls')),
    path('rentals/', include('rentals.urls')),
    path('payments/', include('payments.urls')),
]
