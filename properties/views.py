from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, ProtectedError
from .models import Property
from .forms import PropertyForm
from accounts.permissions import admin_required


@login_required
def property_list(request):
    query = request.GET.get('q', '').strip()
    p_type = request.GET.get('property_type', '').strip()
    status = request.GET.get('status', '').strip()
    city = request.GET.get('city', '').strip()

    properties = Property.objects.all()

    if query:
        properties = properties.filter(
            Q(name__icontains=query) |
            Q(property_code__icontains=query) |
            Q(address__icontains=query) |
            Q(city__icontains=query)
        )

    if p_type:
        properties = properties.filter(property_type=p_type)

    if status:
        properties = properties.filter(status=status)

    if city:
        properties = properties.filter(city__iexact=city)

    # Distinct cities for filter dropdown
    available_cities = Property.objects.values_list('city', flat=True).distinct().order_by('city')

    paginator = Paginator(properties, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Preserve search & filter parameters for pagination links
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    extra_query = f"&{query_params.urlencode()}" if query_params else ""

    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_type': p_type,
        'selected_status': status,
        'selected_city': city,
        'available_cities': available_cities,
        'property_types': Property.PROPERTY_TYPES,
        'status_choices': Property.STATUS_CHOICES,
        'extra_query': extra_query,
    }
    return render(request, 'properties/property_list.html', context)


@login_required
def property_detail(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    active_rental = prop.active_rental
    historical_rentals = prop.rentals.exclude(status='Active').order_by('-start_date')

    context = {
        'property': prop,
        'active_rental': active_rental,
        'historical_rentals': historical_rentals,
    }
    return render(request, 'properties/property_detail.html', context)


@login_required
def property_create(request):
    if request.method == 'POST':
        form = PropertyForm(request.POST)
        if form.is_valid():
            prop = form.save()
            messages.success(request, f"Property '{prop.name}' ({prop.property_code}) was created successfully.")
            return redirect('property_detail', pk=prop.pk)
    else:
        form = PropertyForm()

    return render(request, 'properties/property_form.html', {
        'form': form,
        'title': 'Add New Property',
        'is_edit': False,
    })


@login_required
def property_update(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=prop)
        if form.is_valid():
            prop = form.save()
            messages.success(request, f"Property '{prop.name}' was updated successfully.")
            return redirect('property_detail', pk=prop.pk)
    else:
        form = PropertyForm(instance=prop)

    return render(request, 'properties/property_form.html', {
        'form': form,
        'title': f'Edit Property: {prop.name}',
        'is_edit': True,
        'property': prop,
    })


@login_required
@admin_required
def property_delete(request, pk):
    prop = get_object_or_404(Property, pk=pk)

    if request.method == 'POST':
        # Check if property has an active rental agreement
        if prop.has_active_rental():
            messages.error(
                request,
                f"Cannot delete property '{prop.name}' because it currently has an active rental agreement ({prop.active_rental.rental_number})."
            )
            return redirect('property_detail', pk=prop.pk)

        # Check if property has historical rental records protected by database
        try:
            prop_name = prop.name
            prop_code = prop.property_code
            prop.delete()
            messages.success(request, f"Property '{prop_name}' ({prop_code}) was safely deleted.")
            return redirect('property_list')
        except ProtectedError:
            messages.error(
                request,
                f"Cannot delete property '{prop.name}' because existing rental agreement and financial records depend on it."
            )
            return redirect('property_detail', pk=prop.pk)

    return render(request, 'properties/property_confirm_delete.html', {'property': prop})
