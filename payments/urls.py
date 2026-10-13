from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('record/', views.payment_create, name='payment_create'),
    path('<int:pk>/', views.payment_detail, name='payment_detail'),
    path('<int:pk>/receipt/', views.payment_receipt, name='payment_receipt'),
    path('<int:pk>/delete/', views.payment_delete, name='payment_delete'),
]
