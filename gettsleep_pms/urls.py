from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Вход для персонала — после логина идёт на /dashboard/
    path('staff/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='login'),

    # Выход — для всех пользователей, редирект на главную
    path('staff/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('guest/logout/', auth_views.LogoutView.as_view(next_page='/'), name='guest_logout_staff'),

    # Staff-панель (защищена @staff_required на уровне views)
    path('dashboard/', include('apps.core.urls')),
    path('bookings/', include('apps.bookings.urls')),
    path('rooms/', include('apps.rooms.urls')),
    path('cleaning/', include('apps.cleaning.urls')),
    path('reports/', include('apps.reports.urls')),

    # Публичный сайт и личный кабинет гостя (корень)
    path('', include('apps.guest.urls')),
]
