from django.contrib import admin
from .models import Capsule


@admin.register(Capsule)
class CapsuleAdmin(admin.ModelAdmin):
    list_display = ['number', 'capsule_type', 'floor', 'status', 'price_per_hour', 'is_active']
    list_filter = ['capsule_type', 'status', 'floor', 'is_active']
    search_fields = ['number']
    list_editable = ['status', 'is_active']
