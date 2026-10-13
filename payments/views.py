from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Payment
from .forms import PaymentForm
from rentals.models import RentalAgreement, RentCharge
from accounts.permissions import admin_required


@login_required
def payment_list(request):
    query = request.GET.get('q', '').strip()
    method = request.GET.get('payment_method', '').strip()
    pay_date = request.GET.get('payment_date', '').strip()

    payments = Payment.objects.select_related(
        'rental__property',
        'rental__tenant',
        'rent_charge'
    ).all()

    if query:
        payments = payments.filter(
            Q(payment_number__icontains=query) |
            Q(rental__tenant__full_name__icontains=query) |
            Q(rental__rental_number__icontains=query) |
            Q(reference__icontains=query)
        )

    if method:
        payments = payments.filter(payment_method=method)

    if pay_date:
        payments = payments.filter(payment_date=pay_date)

    paginator = Paginator(payments, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    extra_query = f"&{query_params.urlencode()}" if query_params else ""

    context = {
        'page_obj': page_obj,
        'query': query,
        'selected_method': method,
        'payment_date': pay_date,
        'payment_methods': Payment.PAYMENT_METHODS,
        'extra_query': extra_query,
    }
    return render(request, 'payments/payment_list.html', context)


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related(
            'rental__property',
            'rental__tenant',
            'rent_charge'
        ),
        pk=pk
    )
    context = {
        'payment': payment,
    }
    return render(request, 'payments/payment_detail.html', context)


@login_required
def payment_create(request):
    rental_id = request.GET.get('rental')
    charge_id = request.GET.get('charge')

    rental = None
    charge = None

    if charge_id:
        charge = RentCharge.objects.filter(pk=charge_id).first()
        if charge:
            rental = charge.rental

    if not rental and rental_id:
        rental = RentalAgreement.objects.filter(pk=rental_id).first()

    if request.method == 'POST':
        form = PaymentForm(
            request.POST,
            rental_initial=rental,
            charge_initial=charge
        )
        if form.is_valid():
            payment = form.save()
            messages.success(
                request,
                f"Payment {payment.payment_number} of ${payment.amount} recorded successfully."
            )
            return redirect('payment_detail', pk=payment.pk)
    else:
        form = PaymentForm(
            rental_initial=rental,
            charge_initial=charge
        )

    return render(request, 'payments/payment_form.html', {
        'form': form,
        'rental': rental,
        'charge': charge,
        'title': 'Record Rent Payment',
    })


@login_required
def payment_receipt(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related(
            'rental__property',
            'rental__tenant',
            'rent_charge'
        ),
        pk=pk
    )
    charge = payment.rent_charge

    context = {
        'payment': payment,
        'charge': charge,
        'rental': payment.rental,
        'tenant': payment.rental.tenant,
        'property': payment.rental.property,
    }
    return render(request, 'payments/receipt.html', context)


@login_required
@admin_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    rental_pk = payment.rental.pk

    if request.method == 'POST':
        p_num = payment.payment_number
        p_amt = payment.amount
        payment.delete()
        messages.success(request, f"Payment record {p_num} (${p_amt}) was deleted by administrator.")
        return redirect('rental_detail', pk=rental_pk)

    return render(request, 'payments/payment_confirm_delete.html', {'payment': payment})
