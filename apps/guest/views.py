from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import GuestUser
from apps.rooms.models import Capsule
from apps.bookings.models import Booking, Guest
import datetime


# ─── Вспомогательный декоратор для гостей ─────────────────────────

def guest_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/guest/login/')
        if request.user.is_staff:
            return redirect('/dashboard/')
        return view_func(request, *args, **kwargs)
    return wrapper


def get_capsule_status_for_period(capsule, check_in=None, check_out=None):
    """
    Возвращает реальный статус капсулы с учётом активных бронирований.
    Если даты не переданы — проверяет относительно текущего момента.
    """
    now = timezone.now()
    ci = check_in or now
    co = check_out or now

    # Есть активное заселение в этот период?
    is_occupied = Booking.objects.filter(
        capsule=capsule,
        status='checked_in',
        check_in__lt=co,
        check_out__gt=ci,
    ).exists()
    if is_occupied:
        return 'occupied'

    # Есть подтверждённое бронирование в этот период?
    is_booked = Booking.objects.filter(
        capsule=capsule,
        status='confirmed',
        check_in__lt=co,
        check_out__gt=ci,
    ).exists()
    if is_booked:
        return 'booked'

    # Капсула на уборке?
    if capsule.status == 'cleaning':
        return 'cleaning'

    # Иначе — свободна (или готова)
    if capsule.status == 'ready':
        return 'ready'

    return 'free'


# ─── Публичные страницы ───────────────────────────────────────────

def index(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('/dashboard/')

    capsule_counts = {
        'single': Capsule.objects.filter(capsule_type='single', is_active=True).count(),
        'double': Capsule.objects.filter(capsule_type='double', is_active=True).count(),
        'family': Capsule.objects.filter(capsule_type='family', is_active=True).count(),
    }
    free_count = Capsule.objects.filter(is_active=True).count()
    prices = {
        'single': Capsule.objects.filter(capsule_type='single', is_active=True).values_list('price_per_hour', flat=True).first() or 600,
        'double': Capsule.objects.filter(capsule_type='double', is_active=True).values_list('price_per_hour', flat=True).first() or 900,
        'family': Capsule.objects.filter(capsule_type='family', is_active=True).values_list('price_per_hour', flat=True).first() or 1200,
    }
    return render(request, 'guest/index.html', {
        'capsule_counts': capsule_counts,
        'free_count': free_count,
        'prices': prices,
    })


def guest_register(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('/dashboard/')
        return redirect('guest_cabinet')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        passport = request.POST.get('passport_number', '').strip()
        nationality = request.POST.get('nationality', 'Россия').strip()

        errors = []
        if not username:
            errors.append('Введите логин.')
        if User.objects.filter(username=username).exists():
            errors.append('Такой логин уже занят.')
        if not email:
            errors.append('Введите email.')
        if User.objects.filter(email=email).exists():
            errors.append('Этот email уже зарегистрирован.')
        if len(password1) < 8:
            errors.append('Пароль должен быть не менее 8 символов.')
        if password1 != password2:
            errors.append('Пароли не совпадают.')
        if not first_name or not last_name:
            errors.append('Введите имя и фамилию.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'guest/register.html', {'form_data': request.POST})

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            is_staff=False,
        )
        GuestUser.objects.create(
            user=user,
            phone=phone,
            passport_number=passport,
            nationality=nationality,
        )
        login(request, user)
        messages.success(request, f'Добро пожаловать, {first_name}! Вы успешно зарегистрированы.')
        return redirect('guest_cabinet')

    return render(request, 'guest/register.html', {})


def guest_login(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('/dashboard/')
        return redirect('guest_cabinet')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            if user.is_staff:
                messages.error(request, 'Для входа персонала используйте /staff/login/')
                return render(request, 'guest/login.html', {})
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or '/guest/cabinet/'
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный логин или пароль.')

    return render(request, 'guest/login.html', {'next': request.GET.get('next', '')})


def guest_logout(request):
    logout(request)
    return redirect('guest_index')


# ─── Личный кабинет ──────────────────────────────────────────────

@guest_required
def guest_cabinet(request):
    profile, _ = GuestUser.objects.get_or_create(user=request.user)

    my_bookings = Booking.objects.filter(
        Q(guest__email=request.user.email) |
        Q(guest__first_name=request.user.first_name, guest__last_name=request.user.last_name)
    ).select_related('capsule').order_by('-created_at')

    active = my_bookings.filter(status__in=['confirmed', 'checked_in'])
    history = my_bookings.filter(status__in=['checked_out', 'cancelled'])

    return render(request, 'guest/cabinet.html', {
        'profile': profile,
        'active_bookings': active,
        'history_bookings': history[:10],
    })


@guest_required
def guest_profile_edit(request):
    profile, _ = GuestUser.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()

        profile.phone = request.POST.get('phone', '').strip()
        profile.passport_number = request.POST.get('passport_number', '').strip()
        profile.nationality = request.POST.get('nationality', 'Россия').strip()
        profile.save()

        messages.success(request, 'Профиль обновлён.')
        return redirect('guest_cabinet')

    return render(request, 'guest/profile_edit.html', {'profile': profile})


# ─── Список капсул с динамическим статусом ───────────────────────

def guest_rooms(request):
    check_in_str  = request.GET.get('check_in', '')
    check_out_str = request.GET.get('check_out', '')
    capsule_type  = request.GET.get('capsule_type', '')

    capsules = Capsule.objects.filter(is_active=True).order_by('capsule_type', 'price_per_hour')
    if capsule_type:
        capsules = capsules.filter(capsule_type=capsule_type)

    now = timezone.now()

    check_in = check_out = None
    search_performed = False
    if check_in_str and check_out_str:
        try:
            check_in  = datetime.datetime.fromisoformat(check_in_str)
            check_out = datetime.datetime.fromisoformat(check_out_str)
            if check_out > check_in:
                search_performed = True
            else:
                check_in = check_out = None
        except ValueError:
            pass

    # Без дат — показываем кто занят прямо сейчас (period = 1 секунда)
    ci = check_in  if search_performed else now
    co = check_out if search_performed else (now + datetime.timedelta(seconds=1))

    occupied_ids = set(Booking.objects.filter(
        status='checked_in',
        check_in__lt=co,
        check_out__gt=ci,
    ).values_list('capsule_id', flat=True))

    booked_ids = set(Booking.objects.filter(
        status='confirmed',
        check_in__lt=co,
        check_out__gt=ci,
    ).values_list('capsule_id', flat=True))

    cleaning_ids = set(
        Capsule.objects.filter(status='cleaning', is_active=True)
        .values_list('id', flat=True)
    )

    capsule_list = []
    for c in capsules:
        if c.id in occupied_ids:
            c.computed_status = 'occupied'
            c.is_available = False
        elif c.id in booked_ids:
            c.computed_status = 'booked'
            c.is_available = False
        elif c.id in cleaning_ids:
            c.computed_status = 'cleaning'
            c.is_available = False
        else:
            c.computed_status = 'free'
            c.is_available = True
        capsule_list.append(c)

    from apps.rooms.models import CAPSULE_TYPE_CHOICES
    return render(request, 'guest/rooms.html', {
        'capsules': capsule_list,
        'capsule_types': CAPSULE_TYPE_CHOICES,
        'check_in':  check_in_str,
        'check_out': check_out_str,
        'capsule_type': capsule_type,
        'search_performed': search_performed,
    })


# ─── Бронирование ────────────────────────────────────────────────

@guest_required
def guest_booking_create(request, capsule_id):
    capsule = get_object_or_404(Capsule, pk=capsule_id, is_active=True)

    if request.method == 'POST':
        check_in_str = request.POST.get('check_in', '')
        check_out_str = request.POST.get('check_out', '')

        try:
            check_in = datetime.datetime.fromisoformat(check_in_str)
            check_out = datetime.datetime.fromisoformat(check_out_str)
        except ValueError:
            messages.error(request, 'Неверный формат дат.')
            return redirect('guest_booking_create', capsule_id=capsule_id)

        if check_out <= check_in:
            messages.error(request, 'Дата выезда должна быть позже даты заезда.')
            return redirect('guest_booking_create', capsule_id=capsule_id)

        conflict = Booking.objects.filter(
            capsule=capsule,
            status__in=['confirmed', 'checked_in'],
            check_in__lt=check_out,
            check_out__gt=check_in,
        ).exists()
        if conflict:
            messages.error(request, 'К сожалению, эта капсула уже занята на выбранное время.')
            return redirect('guest_rooms')

        profile, _ = GuestUser.objects.get_or_create(user=request.user)
        passport = profile.passport_number or f'USER_{request.user.pk}'

        guest_obj, _ = Guest.objects.get_or_create(
            passport_number=passport,
            defaults={
                'first_name': request.user.first_name or request.user.username,
                'last_name': request.user.last_name or '',
                'email': request.user.email,
                'phone': profile.phone,
                'nationality': profile.nationality,
            }
        )
        guest_obj.first_name = request.user.first_name or request.user.username
        guest_obj.last_name = request.user.last_name or ''
        guest_obj.email = request.user.email
        guest_obj.phone = profile.phone
        guest_obj.save()

        booking = Booking(
            guest=guest_obj,
            capsule=capsule,
            check_in=check_in,
            check_out=check_out,
            source='site',
            payment_method=request.POST.get('payment_method', 'card'),
            has_towel='has_towel' in request.POST,
            has_slippers='has_slippers' in request.POST,
            has_hygiene='has_hygiene' in request.POST,
            has_meal='has_meal' in request.POST,
            notes=request.POST.get('notes', ''),
        )
        booking.total_amount = booking.calculate_total()
        booking.save()

        messages.success(request, f'Бронирование №{booking.pk} успешно создано! Ждём вас.')
        return redirect('guest_booking_success', pk=booking.pk)

    now = timezone.now()
    check_in_default = request.GET.get('check_in', now.strftime('%Y-%m-%dT%H:00'))
    check_out_default = request.GET.get('check_out', (now + datetime.timedelta(hours=8)).strftime('%Y-%m-%dT%H:00'))

    return render(request, 'guest/booking_form.html', {
        'capsule': capsule,
        'check_in_default': check_in_default,
        'check_out_default': check_out_default,
    })


@guest_required
def guest_booking_success(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    return render(request, 'guest/booking_success.html', {'booking': booking})


@guest_required
def guest_booking_cancel(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    is_owner = (
        booking.guest.email == request.user.email or
        (booking.guest.first_name == request.user.first_name and
         booking.guest.last_name == request.user.last_name)
    )

    if not is_owner:
        messages.error(request, 'У вас нет прав для отмены этого бронирования.')
        return redirect('guest_cabinet')

    if booking.status == 'confirmed':
        booking.status = 'cancelled'
        booking.save()
        booking.capsule.status = 'free'
        booking.capsule.save()
        messages.warning(request, f'Бронирование №{booking.pk} отменено.')
    else:
        messages.error(request, 'Это бронирование нельзя отменить.')

    return redirect('guest_cabinet')
