from django.urls import path
from . import views

urlpatterns = [
    path('', views.tenant_list, name='tenant_list'),
    path('add/', views.tenant_create, name='tenant_create'),
    path('<int:pk>/', views.tenant_detail, name='tenant_detail'),
    path('<int:pk>/edit/', views.tenant_update, name='tenant_update'),
    path('<int:pk>/delete/', views.tenant_delete, name='tenant_delete'),
]
