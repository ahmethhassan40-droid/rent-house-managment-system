import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, ProtectedError
from .models import RentalAgreement, RentCharge
from .forms import RentalAgreementForm, RentalStatusForm, RentChargeForm
from properties.models import Property
from tenants.models import Tenant
from accounts.permissions import admin_required


@login_required
def rental_list(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    rentals = RentalAgreement.objects.select_related('property', 'tenant').all()

    if query:
        rentals = rentals.filter(
            Q(rental_number__icontains=query) |
            Q(tenant__full_name__icontains=query) |
            Q(tenant__phone__icontains=query) |
            Q(property__name__icontains=query) |
            Q(property__property_code__icontains=query)
        )

    if status:
        rentals = rentals.filter(status=status)

    if start_date:
        rentals = rentals.filter(start_date__gte=start_date)

    if end_date:
        rentals = rentals.filter(end_date__lte=end_date)

    paginator = Paginator(rentals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    extra_query = f"&{query_params.urlencode()}" if query_params else ""

    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_status': status,
        'start_date': start_date,
        'end_date': end_date,
        'status_choices': RentalAgreement.STATUS_CHOICES,
        'extra_query': extra_query,
    }
    return render(request, 'rentals/rental_list.html', context)


@login_required
def rental_detail(request, pk):
    rental = get_object_or_404(
        RentalAgreement.objects.select_related('property', 'tenant'),
        pk=pk
    )
    charges = rental.charges.all().order_by('-billing_month')
    payments = rental.payments.select_related('rent_charge').all().order_by('-payment_date', '-created_at')
    status_form = RentalStatusForm(instance=rental)

    context = {
        'rental': rental,
        'charges': charges,
        'payments': payments,
        'status_form': status_form,
    }
    return render(request, 'rentals/rental_detail.html', context)


@login_required
def rental_create(request):
    initial = {}
    prop_id = request.GET.get('property')
    tenant_id = request.GET.get('tenant')

    if prop_id:
        prop = Property.objects.filter(pk=prop_id).first()
        if prop:
            initial['property'] = prop
            initial['monthly_rent'] = prop.monthly_rent

    if tenant_id:
        tenant = Tenant.objects.filter(pk=tenant_id).first()
        if tenant:
            initial['tenant'] = tenant

    if request.method == 'POST':
        form = RentalAgreementForm(request.POST)
        if form.is_valid():
            rental = form.save()
            messages.success(request, f"Rental Agreement {rental.rental_number} created successfully.")
            return redirect('rental_detail', pk=rental.pk)
    else:
        form = RentalAgreementForm(initial=initial)

    return render(request, 'rentals/rental_form.html', {
        'form': form,
        'title': 'Create Rental Agreement',
        'is_edit': False,
    })


@login_required
def rental_update(request, pk):
    rental = get_object_or_404(RentalAgreement, pk=pk)
    if request.method == 'POST':
        form = RentalAgreementForm(request.POST, instance=rental)
        if form.is_valid():
            rental = form.save()
            messages.success(request, f"Rental Agreement {rental.rental_number} updated successfully.")
            return redirect('rental_detail', pk=rental.pk)
    else:
        form = RentalAgreementForm(instance=rental)

    return render(request, 'rentals/rental_form.html', {
        'form': form,
        'title': f'Edit Agreement: {rental.rental_number}',
        'is_edit': True,
        'rental': rental,
    })


@login_required
def rental_status_update(request, pk):
    rental = get_object_or_404(RentalAgreement, pk=pk)
    if request.method == 'POST':
        form = RentalStatusForm(request.POST, instance=rental)
        if form.is_valid():
            rental = form.save()
            messages.success(request, f"Agreement {rental.rental_number} status changed to {rental.status}.")
        else:
            messages.error(request, "Failed to update agreement status.")
    return redirect('rental_detail', pk=rental.pk)


@login_required
@admin_required
def rental_delete(request, pk):
    rental = get_object_or_404(RentalAgreement, pk=pk)

    if request.method == 'POST':
        if rental.charges.exists() or rental.payments.exists():
            messages.error(
                request,
                f"Cannot delete rental agreement {rental.rental_number} because existing financial records (charges or payments) depend on it."
            )
            return redirect('rental_detail', pk=rental.pk)

        try:
            r_num = rental.rental_number
            # If active, deleting should revert property to Available
            prop = rental.property
            rental.delete()
            if not prop.has_active_rental() and prop.status != Property.STATUS_MAINTENANCE:
                prop.status = Property.STATUS_AVAILABLE
                prop.save(update_fields=['status'])
            messages.success(request, f"Rental agreement {r_num} was safely deleted.")
            return redirect('rental_list')
        except ProtectedError:
            messages.error(
                request,
                f"Cannot delete rental agreement {rental.rental_number} due to protected database dependencies."
            )
            return redirect('rental_detail', pk=rental.pk)

    return render(request, 'rentals/rental_confirm_delete.html', {'rental': rental})


@login_required
def rental_print_summary(request, pk):
    rental = get_object_or_404(
        RentalAgreement.objects.select_related('property', 'tenant'),
        pk=pk
    )
    charges = rental.charges.all().order_by('billing_month')
    payments = rental.payments.select_related('rent_charge').all().order_by('payment_date')

    context = {
        'rental': rental,
        'charges': charges,
        'payments': payments,
    }
    return render(request, 'rentals/rental_print_summary.html', context)


# ---------------- Rent Charge Views ----------------

@login_required
def rent_charge_list(request):
    query = request.GET.get('q', '').strip()
    month_filter = request.GET.get('month', '').strip()
    status_filter = request.GET.get('status', '').strip()

    charges = RentCharge.objects.select_related('rental__property', 'rental__tenant').all()

    if query:
        charges = charges.filter(
            Q(rental__rental_number__icontains=query) |
            Q(rental__tenant__full_name__icontains=query) |
            Q(rental__property__name__icontains=query) |
            Q(rental__property__property_code__icontains=query)
        )

    if month_filter:
        try:
            parts = month_filter.split('-')
            d = datetime.date(int(parts[0]), int(parts[1]), 1)
            charges = charges.filter(billing_month=d)
        except (ValueError, IndexError):
            pass

    # Note: payment_status is calculated, so we can filter in python if requested or display
    paginator = Paginator(charges, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    extra_query = f"&{query_params.urlencode()}" if query_params else ""

    context = {
        'page_obj': page_obj,
        'query': query,
        'month_filter': month_filter,
        'extra_query': extra_query,
    }
    return render(request, 'rentals/rent_charge_list.html', context)


@login_required
def rent_charge_create(request):
    rental_id = request.GET.get('rental')
    rental = None
    if rental_id:
        rental = RentalAgreement.objects.filter(pk=rental_id).first()

    if request.method == 'POST':
        form = RentChargeForm(request.POST, rental_initial=rental)
        if form.is_valid():
            charge = form.save()
            messages.success(
                request,
                f"Rent charge of ${charge.amount_due} for {charge.billing_month.strftime('%B %Y')} created successfully."
            )
            return redirect('rental_detail', pk=charge.rental.pk)
    else:
        # Prepopulate due date as current date + 5 days or 1st of month
        initial_data = {
            'due_date': datetime.date.today(),
            'billing_month_input': datetime.date.today().strftime('%Y-%m')
        }
        form = RentChargeForm(initial=initial_data, rental_initial=rental)

    return render(request, 'rentals/rent_charge_form.html', {
        'form': form,
        'rental': rental,
        'title': 'Generate Monthly Rent Charge',
    })


@login_required
@admin_required
def rent_charge_delete(request, pk):
    charge = get_object_or_404(RentCharge, pk=pk)
    rental_pk = charge.rental.pk

    if request.method == 'POST':
        if charge.payments.exists():
            messages.error(
                request,
                f"Cannot delete rent charge for {charge.billing_month.strftime('%B %Y')} because recorded payments depend on it."
            )
            return redirect('rental_detail', pk=rental_pk)

        charge_month = charge.billing_month.strftime('%B %Y')
        charge.delete()
        messages.success(request, f"Rent charge for {charge_month} was deleted.")
        return redirect('rental_detail', pk=rental_pk)

    return redirect('rental_detail', pk=rental_pk)
