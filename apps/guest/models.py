from django.db import models
from django.contrib.auth.models import User


class GuestUser(models.Model):
    """Профиль посетителя (гостя хостела)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guest_profile')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    passport_number = models.CharField(max_length=50, blank=True, verbose_name='Документ')
    nationality = models.CharField(max_length=50, default='Россия', verbose_name='Гражданство')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Профиль гостя'
        verbose_name_plural = 'Профили гостей'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username}'
