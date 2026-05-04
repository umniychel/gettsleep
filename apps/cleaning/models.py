from django.db import models
from django.contrib.auth.models import User
from apps.rooms.models import Capsule

CLEANING_TYPE_CHOICES = [
    ('express', 'Экспресс-уборка'),
    ('standard', 'Стандартная уборка'),
    ('deep', 'Генеральная уборка'),
]

CLEANING_STATUS_CHOICES = [
    ('pending', 'Ожидает'),
    ('in_progress', 'Выполняется'),
    ('done', 'Выполнено'),
]

PRIORITY_CHOICES = [
    ('high', 'Высокий'),
    ('normal', 'Обычный'),
    ('low', 'Низкий'),
]


class CleaningTask(models.Model):
    capsule = models.ForeignKey(Capsule, on_delete=models.CASCADE, related_name='cleaning_tasks', verbose_name='Капсула')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='cleaning_tasks', verbose_name='Горничная')
    cleaning_type = models.CharField(max_length=20, choices=CLEANING_TYPE_CHOICES, default='standard', verbose_name='Тип уборки')
    status = models.CharField(max_length=20, choices=CLEANING_STATUS_CHOICES, default='pending', verbose_name='Статус')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal', verbose_name='Приоритет')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Задача на уборку'
        verbose_name_plural = 'Задачи на уборку'
        ordering = ['-created_at']

    def __str__(self):
        return f'Уборка капсулы {self.capsule.number} — {self.get_cleaning_type_display()}'

    def get_status_color(self):
        colors = {
            'pending': 'warning',
            'in_progress': 'info',
            'done': 'success',
        }
        return colors.get(self.status, 'secondary')

    def get_priority_color(self):
        colors = {
            'high': 'danger',
            'normal': 'warning',
            'low': 'secondary',
        }
        return colors.get(self.priority, 'secondary')
