from django.db import models

CAPSULE_TYPE_CHOICES = [
    ('single', 'Одноместная'),
    ('double', 'Двухместная'),
    ('family', 'Семейная'),
]

CAPSULE_STATUS_CHOICES = [
    ('free', 'Свободна'),
    ('booked', 'Забронирована'),
    ('occupied', 'Занята'),
    ('cleaning', 'На уборке'),
    ('ready', 'Готова к заселению'),
]

FLOOR_CHOICES = [(i, f'{i} этаж') for i in range(1, 5)]


class Capsule(models.Model):
    number = models.CharField(max_length=10, unique=True, verbose_name='Номер капсулы')
    capsule_type = models.CharField(max_length=20, choices=CAPSULE_TYPE_CHOICES, default='single', verbose_name='Тип')
    floor = models.IntegerField(choices=FLOOR_CHOICES, default=1, verbose_name='Этаж')
    status = models.CharField(max_length=20, choices=CAPSULE_STATUS_CHOICES, default='free', verbose_name='Статус')
    price_per_hour = models.DecimalField(max_digits=8, decimal_places=2, default=500, verbose_name='Цена/час (руб.)')
    description = models.TextField(blank=True, verbose_name='Описание')
    is_active = models.BooleanField(default=True, verbose_name='Активна')

    class Meta:
        verbose_name = 'Капсула'
        verbose_name_plural = 'Капсулы'
        ordering = ['number']

    def __str__(self):
        return f'Капсула {self.number} ({self.get_capsule_type_display()})'

    def get_status_color(self):
        colors = {
            'free': 'success',
            'booked': 'warning',
            'occupied': 'danger',
            'cleaning': 'info',
            'ready': 'primary',
        }
        return colors.get(self.status, 'secondary')
