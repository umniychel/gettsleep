from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.models import User
from .models import CleaningTask, CLEANING_STATUS_CHOICES, CLEANING_TYPE_CHOICES, PRIORITY_CHOICES
from apps.rooms.models import Capsule
from apps.core.views import log_action
from apps.core.decorators import staff_required


def is_maid(user):
    try:
        return user.profile.role == 'maid'
    except Exception:
        return False


@staff_required
def task_list(request):
    tasks = CleaningTask.objects.select_related(
        'capsule', 'assigned_to'
    ).order_by('status', '-priority', 'created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    # Горничная видит ВСЕ задачи (не только свои):
    # — свободные (assigned_to=None) она может взять
    # — свои (assigned_to=user) — выполнять
    # — чужие in_progress — только просматривать
    # Менеджер/администратор видит всё без фильтров.

    user = request.user
    user_is_maid = is_maid(user)

    context = {
        'tasks': tasks,
        'status_choices': CLEANING_STATUS_CHOICES,
        'current_status': status_filter,
        'user_is_maid': user_is_maid,
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
def task_take(request, pk):
    """Горничная берёт свободную задачу в работу."""
    if request.method != 'POST':
        return redirect('task_list')
    task = get_object_or_404(CleaningTask, pk=pk)
    if task.assigned_to is None and task.status == 'pending':
        task.assigned_to = request.user
        task.status = 'in_progress'
        task.started_at = timezone.now()
        task.save()
        log_action(request, f'Горничная {request.user.get_full_name()} взяла задачу #{task.pk} (капсула {task.capsule.number})', 'CleaningTask', task.pk)
        messages.success(request, f'Вы взяли задачу по уборке капсулы {task.capsule.number}.')
    else:
        messages.error(request, 'Задача уже назначена или не в статусе ожидания.')
    return redirect('task_list')


@staff_required
def task_start(request, pk):
    """Начать уборку (для назначенной горничной или менеджера)."""
    if request.method != 'POST':
        return redirect('task_list')
    task = get_object_or_404(CleaningTask, pk=pk)
    if task.status == 'pending':
        task.status = 'in_progress'
        task.started_at = timezone.now()
        # Если горничная начинает незакреплённую задачу — автоназначаем
        if task.assigned_to is None:
            task.assigned_to = request.user
        task.save()
        log_action(request, f'Начата уборка капсулы {task.capsule.number}', 'CleaningTask', task.pk)
        messages.info(request, f'Уборка капсулы {task.capsule.number} начата.')
    return redirect('task_list')


@staff_required
def task_complete(request, pk):
    """Завершить уборку."""
    if request.method != 'POST':
        return redirect('task_list')
    task = get_object_or_404(CleaningTask, pk=pk)
    if task.status in ('pending', 'in_progress'):
        # Если горничная завершает незакреплённую — фиксируем её
        if task.assigned_to is None:
            task.assigned_to = request.user
        task.status = 'done'
        task.completed_at = timezone.now()
        task.save()
        task.capsule.status = 'ready'
        task.capsule.save()
        log_action(request, f'Завершена уборка капсулы {task.capsule.number} — {request.user.get_full_name()}', 'CleaningTask', task.pk)
        messages.success(request, f'Уборка капсулы {task.capsule.number} завершена. Статус: готова к заселению.')
    return redirect('task_list')
