from django.shortcuts import render, redirect
from django.utils import timezone
from apps.rooms.models import Capsule
from apps.bookings.models import Booking
from apps.cleaning.models import CleaningTask
from apps.core.models import AuditLog
from apps.core.decorators import staff_required


def log_action(request, action, model_name='', object_id=None, details=''):
    ip = request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        user=request.user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        details=details,
        ip_address=ip,
    )


@staff_required
def dashboard(request):
    today = timezone.localdate()

    total_capsules = Capsule.objects.filter(is_active=True).count()
    free_capsules = Capsule.objects.filter(status='free', is_active=True).count()
    occupied_capsules = Capsule.objects.filter(status='occupied', is_active=True).count()
    cleaning_capsules = Capsule.objects.filter(status='cleaning', is_active=True).count()

    today_bookings = Booking.objects.filter(created_at__date=today).count()
    active_bookings = Booking.objects.filter(status='checked_in').count()
    pending_tasks = CleaningTask.objects.filter(status='pending').count()
    high_priority_tasks = CleaningTask.objects.filter(status='pending', priority='high').count()

    recent_bookings = Booking.objects.select_related('guest', 'capsule').order_by('-created_at')[:8]
    pending_cleaning = CleaningTask.objects.select_related('capsule', 'assigned_to').filter(
        status__in=['pending', 'in_progress']
    ).order_by('priority', 'created_at')[:8]

    capsules = Capsule.objects.filter(is_active=True).order_by('number')

    context = {
        'total_capsules': total_capsules,
        'free_capsules': free_capsules,
        'occupied_capsules': occupied_capsules,
        'cleaning_capsules': cleaning_capsules,
        'today_bookings': today_bookings,
        'active_bookings': active_bookings,
        'pending_tasks': pending_tasks,
        'high_priority_tasks': high_priority_tasks,
        'recent_bookings': recent_bookings,
        'pending_cleaning': pending_cleaning,
        'capsules': capsules,
        'page': 'dashboard',
    }
    return render(request, 'dashboard.html', context)
