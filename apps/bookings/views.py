from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Booking, Guest, BOOKING_STATUS_CHOICES, SOURCE_CHOICES, PAYMENT_METHOD_CHOICES
from apps.rooms.models import Capsule
from apps.cleaning.models import CleaningTask
from apps.core.views import log_action
from apps.core.decorators import staff_required
import datetime


@staff_required
def booking_list(request):
    bookings = Booking.objects.select_related('guest', 'capsule').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    if search:
        bookings = bookings.filter(
            Q(guest__last_name__icontains=search) |
            Q(guest__first_name__icontains=search) |
            Q(capsule__number__icontains=search) |
            Q(guest__passport_number__icontains=search)
        )
    context = {
        'bookings': bookings[:100],
        'status_choices': BOOKING_STATUS_CHOICES,
        'current_status': status_filter,
        'search': search,
        'page': 'bookings',
    }
    return render(request, 'bookings/list.html', context)


@staff_required
def booking_create(request):
    if request.method == 'POST':
        guest_id = request.POST.get('guest_id')
        if guest_id:
            guest = get_object_or_404(Guest, pk=guest_id)
        else:
            guest = Guest(
                first_name=request.POST['first_name'],
                last_name=request.POST['last_name'],
                middle_name=request.POST.get('middle_name', ''),
                passport_number=request.POST['passport_number'],
                phone=request.POST.get('phone', ''),
                email=request.POST.get('email', ''),
                nationality=request.POST.get('nationality', 'Россия'),
            )
            guest.save()

        capsule = get_object_or_404(Capsule, pk=request.POST['capsule_id'])
        check_in = datetime.datetime.fromisoformat(request.POST['check_in'])
        check_out = datetime.datetime.fromisoformat(request.POST['check_out'])

        booking = Booking(
            guest=guest,
            capsule=capsule,
            check_in=check_in,
            check_out=check_out,
            source=request.POST.get('source', 'reception'),
            payment_method=request.POST.get('payment_method', 'cash'),
            has_towel='has_towel' in request.POST,
            has_slippers='has_slippers' in request.POST,
            has_hygiene='has_hygiene' in request.POST,
            has_meal='has_meal' in request.POST,
            notes=request.POST.get('notes', ''),
        )
        booking.total_amount = booking.calculate_total()
        booking.save()

        capsule.status = 'booked'
        capsule.save()

        log_action(request, f'Создано бронирование #{booking.pk}', 'Booking', booking.pk)
        messages.success(request, f'Бронирование #{booking.pk} создано.')
        return redirect('booking_detail', pk=booking.pk)

    free_capsules = Capsule.objects.filter(status__in=['free', 'ready'], is_active=True)
    guests = Guest.objects.order_by('-created_at')[:50]
    context = {
        'free_capsules': free_capsules,
        'guests': guests,
        'sources': SOURCE_CHOICES,
        'payment_methods': PAYMENT_METHOD_CHOICES,
        'page': 'bookings',
    }
    return render(request, 'bookings/form.html', context)


@staff_required
def booking_detail(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    context = {'booking': booking, 'page': 'bookings'}
    return render(request, 'bookings/detail.html', context)


@staff_required
def booking_checkin(request, pk):
    if request.method != 'POST':
        return redirect('booking_detail', pk=pk)
    booking = get_object_or_404(Booking, pk=pk)
    if booking.status == 'confirmed':
        booking.status = 'checked_in'
        booking.is_paid = True
        booking.save()
        booking.capsule.status = 'occupied'
        booking.capsule.save()
        log_action(request, f'Заезд по бронированию #{booking.pk}', 'Booking', booking.pk)
        messages.success(request, f'Гость {booking.guest} заселён в капсулу {booking.capsule.number}.')
    return redirect('booking_detail', pk=pk)


@staff_required
def booking_checkout(request, pk):
    if request.method != 'POST':
        return redirect('booking_detail', pk=pk)
    booking = get_object_or_404(Booking, pk=pk)
    if booking.status == 'checked_in':
        booking.status = 'checked_out'
        booking.save()
        capsule = booking.capsule
        capsule.status = 'cleaning'
        capsule.save()
        task = CleaningTask.objects.create(
            capsule=capsule,
            cleaning_type='express',
            priority='high',
        )
        log_action(request, f'Выезд по бронированию #{booking.pk}, создана задача уборки #{task.pk}', 'Booking', booking.pk)
        messages.success(request, f'Выезд оформлен. Создана задача на уборку капсулы {capsule.number}.')
    return redirect('booking_detail', pk=pk)


@staff_required
def booking_cancel(request, pk):
    if request.method != 'POST':
        return redirect('booking_detail', pk=pk)
    booking = get_object_or_404(Booking, pk=pk)
    if booking.status in ('confirmed',):
        booking.status = 'cancelled'
        booking.save()
        booking.capsule.status = 'free'
        booking.capsule.save()
        log_action(request, f'Отменено бронирование #{booking.pk}', 'Booking', booking.pk)
        messages.warning(request, 'Бронирование отменено.')
    return redirect('booking_list')
