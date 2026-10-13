from decimal import Decimal
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from properties.models import Property
from tenants.models import Tenant
from rentals.models import RentalAgreement, RentCharge
from payments.models import Payment


@login_required
def dashboard_view(request):
    # Core Property Statistics
    total_properties = Property.objects.count()
    available_properties = Property.objects.filter(status=Property.STATUS_AVAILABLE).count()
    rented_properties = Property.objects.filter(status=Property.STATUS_RENTED).count()
    maintenance_properties = Property.objects.filter(status=Property.STATUS_MAINTENANCE).count()

    # Tenant and Rental Statistics
    total_tenants = Tenant.objects.count()
    active_rentals = RentalAgreement.objects.filter(status=RentalAgreement.STATUS_ACTIVE).count()

    # Financial Metrics (Calculated strictly from database queries)
    # Total rent collected is the sum of all recorded payments
    total_rent_collected = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Total billed charges
    total_charges_billed = RentCharge.objects.aggregate(total=Sum('amount_due'))['total'] or Decimal('0.00')

    # Pending rent balance: unpaid portion of recorded rent charges
    pending_rent_balance = max(Decimal('0.00'), total_charges_billed - total_rent_collected)

    # Derived Performance Metrics
    occupancy_rate = int((rented_properties / total_properties) * 100) if total_properties > 0 else 0
    collection_rate = int((total_rent_collected / total_charges_billed) * 100) if total_charges_billed > 0 else 0

    # Charges with pending balance (Actionable for landlord)
    all_charges = RentCharge.objects.select_related(
        'rental__property',
        'rental__tenant'
    ).prefetch_related('payments').order_by('-billing_month')
    pending_charges = [c for c in all_charges if c.outstanding_balance > Decimal('0.00')][:5]

    # Recent Records
    recent_rentals = RentalAgreement.objects.select_related('property', 'tenant').order_by('-created_at')[:5]
    recent_payments = Payment.objects.select_related('rental__tenant', 'rental__property').order_by('-created_at')[:5]

    context = {
        'total_properties': total_properties,
        'available_properties': available_properties,
        'rented_properties': rented_properties,
        'maintenance_properties': maintenance_properties,
        'total_tenants': total_tenants,
        'active_rentals': active_rentals,
        'pending_rent_balance': pending_rent_balance,
        'total_rent_collected': total_rent_collected,
        'total_charges_billed': total_charges_billed,
        'occupancy_rate': occupancy_rate,
        'collection_rate': collection_rate,
        'pending_charges': pending_charges,
        'recent_rentals': recent_rentals,
        'recent_payments': recent_payments,
    }
    return render(request, 'dashboard/dashboard.html', context)
