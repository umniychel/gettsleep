from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def staff_required(view_func):
    """
    Декоратор: пускает только авторизованных сотрудников (is_staff=True).
    Гостей (is_staff=False) перенаправляет в их личный кабинет.
    Неавторизованных — на страницу входа для персонала.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/staff/login/')
        if not request.user.is_staff:
            messages.error(request, 'Доступ запрещён. Этот раздел только для сотрудников.')
            return redirect('guest_cabinet')
        return view_func(request, *args, **kwargs)
    return wrapper
