from django.db import models
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ('admin', 'Администратор ресепшена'),
    ('maid', 'Горничная'),
    ('manager', 'Менеджер'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    phone = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'


class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.IntegerField(null=True, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Журнал аудита'
        verbose_name_plural = 'Журнал аудита'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.created_at:%d.%m.%Y %H:%M} — {self.user} — {self.action}'
