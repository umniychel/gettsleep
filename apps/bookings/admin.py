from django.contrib import admin
from .models import Booking, Guest


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'passport_number', 'phone', 'email', 'nationality', 'created_at']
    search_fields = ['last_name', 'first_name', 'passport_number', 'phone']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['pk', 'guest', 'capsule', 'check_in', 'check_out', 'status', 'total_amount', 'is_paid', 'source']
    list_filter = ['status', 'source', 'payment_method', 'is_paid']
    search_fields = ['guest__last_name', 'guest__first_name', 'capsule__number']
    date_hierarchy = 'created_at'
    list_editable = ['status', 'is_paid']
