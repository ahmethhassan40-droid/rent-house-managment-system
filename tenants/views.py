from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, ProtectedError
from .models import Tenant
from .forms import TenantForm
from accounts.permissions import admin_required
from payments.models import Payment


@login_required
def tenant_list(request):
    query = request.GET.get('q', '').strip()
    tenants = Tenant.objects.all()

    if query:
        tenants = tenants.filter(
            Q(full_name__icontains=query) |
            Q(phone__icontains=query) |
            Q(tenant_number__icontains=query) |
            Q(email__icontains=query)
        )

    paginator = Paginator(tenants, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    extra_query = f"&{query_params.urlencode()}" if query_params else ""

    context = {
        'page_obj': page_obj,
        'query': query,
        'extra_query': extra_query,
    }
    return render(request, 'tenants/tenant_list.html', context)


@login_required
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    active_rentals = tenant.rentals.filter(status='Active')
    all_rentals = tenant.rentals.all().order_by('-start_date')
    # Tenant payment history through their rental agreements
    payment_history = Payment.objects.filter(rental__tenant=tenant).order_by('-payment_date', '-created_at')

    context = {
        'tenant': tenant,
        'active_rentals': active_rentals,
        'all_rentals': all_rentals,
        'payment_history': payment_history,
    }
    return render(request, 'tenants/tenant_detail.html', context)


@login_required
def tenant_create(request):
    if request.method == 'POST':
        form = TenantForm(request.POST)
        if form.is_valid():
            tenant = form.save()
            messages.success(request, f"Tenant '{tenant.full_name}' ({tenant.tenant_number}) was registered successfully.")
            return redirect('tenant_detail', pk=tenant.pk)
    else:
        form = TenantForm()

    return render(request, 'tenants/tenant_form.html', {
        'form': form,
        'title': 'Register New Tenant',
        'is_edit': False,
    })


@login_required
def tenant_update(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)
    if request.method == 'POST':
        form = TenantForm(request.POST, instance=tenant)
        if form.is_valid():
            tenant = form.save()
            messages.success(request, f"Tenant '{tenant.full_name}' was updated successfully.")
            return redirect('tenant_detail', pk=tenant.pk)
    else:
        form = TenantForm(instance=tenant)

    return render(request, 'tenants/tenant_form.html', {
        'form': form,
        'title': f'Edit Tenant: {tenant.full_name}',
        'is_edit': True,
        'tenant': tenant,
    })


@login_required
@admin_required
def tenant_delete(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)

    if request.method == 'POST':
        # Check if tenant has active rental agreements
        if tenant.has_active_rentals():
            messages.error(
                request,
                f"Cannot delete tenant '{tenant.full_name}' because they currently have one or more active rental agreements."
            )
            return redirect('tenant_detail', pk=tenant.pk)

        # Attempt deletion; catch DB protected error for existing historical agreements/payments
        try:
            name = tenant.full_name
            t_num = tenant.tenant_number
            tenant.delete()
            messages.success(request, f"Tenant '{name}' ({t_num}) was safely deleted.")
            return redirect('tenant_list')
        except ProtectedError:
            messages.error(
                request,
                f"Cannot delete tenant '{tenant.full_name}' because existing rental agreements or financial history depend on this record."
            )
            return redirect('tenant_detail', pk=tenant.pk)

    return render(request, 'tenants/tenant_confirm_delete.html', {'tenant': tenant})
