from django.urls import path
from . import views

urlpatterns = [
    path('', views.booking_list, name='booking_list'),
    path('create/', views.booking_create, name='booking_create'),
    path('<int:pk>/', views.booking_detail, name='booking_detail'),
    path('<int:pk>/checkin/', views.booking_checkin, name='booking_checkin'),
    path('<int:pk>/checkout/', views.booking_checkout, name='booking_checkout'),
    path('<int:pk>/cancel/', views.booking_cancel, name='booking_cancel'),
]
