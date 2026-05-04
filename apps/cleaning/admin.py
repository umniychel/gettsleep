from django.contrib import admin
from .models import CleaningTask


@admin.register(CleaningTask)
class CleaningTaskAdmin(admin.ModelAdmin):
    list_display = ['pk', 'capsule', 'cleaning_type', 'priority', 'status', 'assigned_to', 'created_at', 'completed_at']
    list_filter = ['status', 'priority', 'cleaning_type']
    search_fields = ['capsule__number']
    list_editable = ['status', 'priority']
