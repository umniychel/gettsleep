from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count
from apps.bookings.models import Booking
from apps.rooms.models import Capsule
from apps.cleaning.models import CleaningTask
from apps.core.models import AuditLog
from apps.core.decorators import staff_required
import datetime
import json


@staff_required
def reports_main(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    month_bookings = Booking.objects.filter(
        created_at__date__gte=month_start,
        status__in=['checked_in', 'checked_out']
    )
    month_revenue = month_bookings.aggregate(total=Sum('total_amount'))['total'] or 0
    month_count = month_bookings.count()

    today_bookings = Booking.objects.filter(created_at__date=today)
    today_revenue = today_bookings.filter(is_paid=True).aggregate(total=Sum('total_amount'))['total'] or 0

    total_capsules = Capsule.objects.filter(is_active=True).count()
    occupied = Capsule.objects.filter(status='occupied', is_active=True).count()
    occupancy_rate = round((occupied / total_capsules * 100) if total_capsules else 0, 1)

    sources = Booking.objects.filter(
        created_at__date__gte=month_start
    ).values('source').annotate(count=Count('id')).order_by('-count')

    days = []
    revenues = []
    for i in range(13, -1, -1):
        d = today - datetime.timedelta(days=i)
        rev = Booking.objects.filter(
            created_at__date=d, is_paid=True
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        days.append(d.strftime('%d.%m'))
        revenues.append(float(rev))

    audit_logs = AuditLog.objects.select_related('user').order_by('-created_at')[:50]

    context = {
        'month_revenue': month_revenue,
        'month_count': month_count,
        'today_revenue': today_revenue,
        'today_count': today_bookings.count(),
        'occupancy_rate': occupancy_rate,
        'total_capsules': total_capsules,
        'occupied': occupied,
        'sources': sources,
        'days_json': json.dumps(days),
        'revenues_json': json.dumps(revenues),
        'audit_logs': audit_logs,
        'page': 'reports',
    }
    return render(request, 'reports/main.html', context)
