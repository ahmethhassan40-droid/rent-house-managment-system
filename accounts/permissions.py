"""
Role-based permission helpers and decorators for RHMS.
Roles:
1. Admin / Property Manager: full CRUD, delete properties/tenants/payments, user admin.
2. Staff / Receptionist: view properties, register tenants, create agreements, record payments, view details, print receipts. Cannot delete restricted records or manage users.
"""

from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect


def is_admin(user):
    """Check if user has Admin / Property Manager rights."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name='Admin').exists()


def is_staff_member(user):
    """Check if user is at least Staff or Admin."""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff or user.groups.filter(name__in=['Admin', 'Staff']).exists()


def admin_required(view_func):
    """Decorator ensuring the user has Admin rights."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_admin(request.user):
            messages.error(request, "Access denied: You do not have administrator permissions to perform this action.")
            raise PermissionDenied("Administrator privileges required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def staff_required(view_func):
    """Decorator ensuring the user is at least a staff member."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not is_staff_member(request.user):
            messages.error(request, "Access denied: Staff privileges required.")
            raise PermissionDenied("Staff privileges required.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
