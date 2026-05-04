from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .models import CleaningTask, CLEANING_STATUS_CHOICES, CLEANING_TYPE_CHOICES, PRIORITY_CHOICES
from apps.rooms.models import Capsule
from apps.core.views import log_action
from apps.core.decorators import staff_required


@staff_required
def task_list(request):
    tasks = CleaningTask.objects.select_related('capsule', 'assigned_to').order_by('priority', 'created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # Горничная видит только свои задачи
    user = request.user
    try:
        if user.profile.role == 'maid':
            tasks = tasks.filter(assigned_to=user)
    except Exception:
        pass

    context = {
        'tasks': tasks,
        'status_choices': CLEANING_STATUS_CHOICES,
        'current_status': status_filter,
        'page': 'cleaning',
    }
    return render(request, 'cleaning/list.html', context)


@staff_required
def task_create(request):
    if request.method == 'POST':
        capsule = get_object_or_404(Capsule, pk=request.POST['capsule_id'])
        assigned_id = request.POST.get('assigned_to')
        assigned = None
        if assigned_id:
            try:
                assigned = User.objects.get(pk=assigned_id)
            except User.DoesNotExist:
                pass

        task = CleaningTask.objects.create(
            capsule=capsule,
            assigned_to=assigned,
            cleaning_type=request.POST.get('cleaning_type', 'standard'),
            priority=request.POST.get('priority', 'normal'),
            notes=request.POST.get('notes', ''),
        )
        capsule.status = 'cleaning'
        capsule.save()
        log_action(request, f'Создана задача уборки #{task.pk} капсулы {capsule.number}', 'CleaningTask', task.pk)
        messages.success(request, f'Задача на уборку капсулы {capsule.number} создана.')
        return redirect('task_list')

    capsules = Capsule.objects.filter(is_active=True)
    # Получаем горничных безопасно: через профиль или через is_staff
    try:
        maids = User.objects.filter(profile__role='maid', is_active=True)
    except Exception:
        maids = User.objects.filter(is_active=True, is_staff=True)

    context = {
        'capsules': capsules,
        'maids': maids,
        'cleaning_types': CLEANING_TYPE_CHOICES,
        'priorities': PRIORITY_CHOICES,
        'page': 'cleaning',
    }
    return render(request, 'cleaning/form.html', context)


@staff_required
def task_start(request, pk):
    if request.method != 'POST':
        return redirect('task_list')
    task = get_object_or_404(CleaningTask, pk=pk)
    if task.status == 'pending':
        task.status = 'in_progress'
        task.started_at = timezone.now()
        task.assigned_to = request.user
        task.save()
        log_action(request, f'Начата уборка капсулы {task.capsule.number}', 'CleaningTask', task.pk)
        messages.info(request, f'Уборка капсулы {task.capsule.number} начата.')
    return redirect('task_list')


@staff_required
def task_complete(request, pk):
    if request.method != 'POST':
        return redirect('task_list')
    task = get_object_or_404(CleaningTask, pk=pk)
    if task.status in ('pending', 'in_progress'):
        task.status = 'done'
        task.completed_at = timezone.now()
        task.save()
        task.capsule.status = 'ready'
        task.capsule.save()
        log_action(request, f'Завершена уборка капсулы {task.capsule.number}', 'CleaningTask', task.pk)
        messages.success(request, f'Уборка капсулы {task.capsule.number} завершена. Статус: готова к заселению.')
    return redirect('task_list')
