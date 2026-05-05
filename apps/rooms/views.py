from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Capsule, CAPSULE_STATUS_CHOICES, CAPSULE_TYPE_CHOICES
from apps.core.views import log_action
from apps.core.decorators import staff_required, manager_required


@staff_required
def room_list(request):
    capsules = Capsule.objects.filter(is_active=True).order_by('floor', 'number')
    status_filter = request.GET.get('status', '')
    if status_filter:
        capsules = capsules.filter(status=status_filter)
    # Горничная может смотреть капсулы но не управлять
    role = getattr(getattr(request.user, 'profile', None), 'role', 'manager')
    context = {
        'capsules': capsules,
        'status_choices': CAPSULE_STATUS_CHOICES,
        'current_status': status_filter,
        'can_manage': role in ('manager', 'admin') or request.user.is_superuser,
        'page': 'rooms',
    }
    return render(request, 'rooms/list.html', context)


@staff_required
def room_detail(request, pk):
    capsule = get_object_or_404(Capsule, pk=pk)
    recent_bookings = capsule.bookings.select_related('guest').order_by('-created_at')[:10]
    role = getattr(getattr(request.user, 'profile', None), 'role', 'manager')
    context = {
        'capsule': capsule,
        'recent_bookings': recent_bookings,
        'can_manage': role in ('manager', 'admin') or request.user.is_superuser,
        'page': 'rooms',
    }
    return render(request, 'rooms/detail.html', context)


@manager_required
def room_create(request):
    if request.method == 'POST':
        capsule = Capsule(
            number=request.POST['number'],
            capsule_type=request.POST['capsule_type'],
            floor=request.POST['floor'],
            price_per_hour=request.POST['price_per_hour'],
            description=request.POST.get('description', ''),
        )
        capsule.save()
        log_action(request, f'Создана капсула {capsule.number}', 'Capsule', capsule.pk)
        messages.success(request, f'Капсула {capsule.number} создана.')
        return redirect('room_list')
    context = {'capsule_types': CAPSULE_TYPE_CHOICES, 'page': 'rooms'}
    return render(request, 'rooms/form.html', context)


@manager_required
def room_edit(request, pk):
    capsule = get_object_or_404(Capsule, pk=pk)
    if request.method == 'POST':
        capsule.number = request.POST['number']
        capsule.capsule_type = request.POST['capsule_type']
        capsule.floor = request.POST['floor']
        capsule.price_per_hour = request.POST['price_per_hour']
        capsule.description = request.POST.get('description', '')
        capsule.save()
        log_action(request, f'Изменена капсула {capsule.number}', 'Capsule', capsule.pk)
        messages.success(request, 'Данные капсулы обновлены.')
        return redirect('room_list')
    context = {'capsule': capsule, 'capsule_types': CAPSULE_TYPE_CHOICES, 'page': 'rooms'}
    return render(request, 'rooms/form.html', context)


@staff_required
def room_status_change(request, pk):
    if request.method == 'POST':
        role = getattr(getattr(request.user, 'profile', None), 'role', 'manager')
        if role == 'maid':
            messages.error(request, 'Горничные не могут менять статус капсул.')
            return redirect('room_list')
        capsule = get_object_or_404(Capsule, pk=pk)
        new_status = request.POST.get('status')
        if new_status in dict(CAPSULE_STATUS_CHOICES):
            old = capsule.get_status_display()
            capsule.status = new_status
            capsule.save()
            log_action(request, f'Статус капсулы {capsule.number}: {old} → {capsule.get_status_display()}', 'Capsule', capsule.pk)
            messages.success(request, f'Статус обновлён: {capsule.get_status_display()}')
    return redirect('room_list')
