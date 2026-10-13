from django.urls import path
from . import views

urlpatterns = [
    # Rental Agreements
    path('', views.rental_list, name='rental_list'),
    path('add/', views.rental_create, name='rental_create'),
    path('<int:pk>/', views.rental_detail, name='rental_detail'),
    path('<int:pk>/edit/', views.rental_update, name='rental_update'),
    path('<int:pk>/status/', views.rental_status_update, name='rental_status_update'),
    path('<int:pk>/delete/', views.rental_delete, name='rental_delete'),
    path('<int:pk>/print/', views.rental_print_summary, name='rental_print_summary'),

    # Rent Charges
    path('charges/', views.rent_charge_list, name='rent_charge_list'),
    path('charges/add/', views.rent_charge_create, name='rent_charge_create'),
    path('charges/<int:pk>/delete/', views.rent_charge_delete, name='rent_charge_delete'),
]
