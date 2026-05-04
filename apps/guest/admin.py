from django.contrib import admin
from .models import GuestUser


@admin.register(GuestUser)
class GuestUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'passport_number', 'nationality', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'passport_number']
