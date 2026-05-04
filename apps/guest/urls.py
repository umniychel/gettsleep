from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='guest_index'),
    path('guest/register/', views.guest_register, name='guest_register'),
    path('guest/login/', views.guest_login, name='guest_login'),
    path('guest/logout/', views.guest_logout, name='guest_logout'),
    path('guest/cabinet/', views.guest_cabinet, name='guest_cabinet'),
    path('guest/cabinet/edit/', views.guest_profile_edit, name='guest_profile_edit'),
    path('guest/rooms/', views.guest_rooms, name='guest_rooms'),
    path('guest/rooms/<int:capsule_id>/book/', views.guest_booking_create, name='guest_booking_create'),
    path('guest/booking/<int:pk>/success/', views.guest_booking_success, name='guest_booking_success'),
    path('guest/booking/<int:pk>/cancel/', views.guest_booking_cancel, name='guest_booking_cancel'),
]
