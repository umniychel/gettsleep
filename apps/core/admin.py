from django.contrib import admin
from .models import UserProfile, AuditLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'phone']
    list_filter = ['role']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['created_at', 'user', 'action', 'model_name', 'ip_address']
    list_filter = ['model_name']
    search_fields = ['action', 'user__username']
    readonly_fields = ['created_at', 'user', 'action', 'model_name', 'object_id', 'details', 'ip_address']
