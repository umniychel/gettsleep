from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def staff_required(view_func):
    """Только авторизованные сотрудники (is_staff=True)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/staff/login/')
        if not request.user.is_staff:
            messages.error(request, 'Доступ запрещён. Этот раздел только для сотрудников.')
            return redirect('/guest/cabinet/')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_or_admin_required(view_func):
    """Только менеджер или администратор ресепшена (не горничная)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/staff/login/')
        if not request.user.is_staff:
            return redirect('/guest/cabinet/')
        # Горничным — запрещено
        if hasattr(request.user, 'profile') and request.user.profile.role == 'maid':
            messages.error(request, 'Доступ запрещён. Этот раздел недоступен для горничных.')
            return redirect('/cleaning/')
        return view_func(request, *args, **kwargs)
    return wrapper


def manager_required(view_func):
    """Только менеджер (добавление/изменение капсул, полный доступ)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/staff/login/')
        if not request.user.is_staff:
            return redirect('/guest/cabinet/')
        role = getattr(getattr(request.user, 'profile', None), 'role', None)
        if role not in ('manager', None) and not request.user.is_superuser:
            messages.error(request, 'Доступ запрещён. Только для менеджеров.')
            return redirect('/dashboard/')
        return view_func(request, *args, **kwargs)
    return wrapper
