from django.db import models
from apps.rooms.models import Capsule

BOOKING_STATUS_CHOICES = [
    ('confirmed', 'Подтверждено'),
    ('checked_in', 'Заселён'),
    ('checked_out', 'Выселен'),
    ('cancelled', 'Отменено'),
]

SOURCE_CHOICES = [
    ('site', 'Сайт хостела'),
    ('booking', 'Booking.com'),
    ('airbnb', 'Airbnb'),
    ('reception', 'Стойка регистрации'),
]

PAYMENT_METHOD_CHOICES = [
    ('cash', 'Наличные'),
    ('card', 'Банковская карта'),
    ('sbp', 'СБП'),
]

EXTRA_SERVICE_CHOICES = [
    ('towel', 'Полотенце', 150),
    ('slippers', 'Тапочки', 100),
    ('hygiene', 'Гигиенический набор', 200),
    ('meal', 'Питание', 350),
]


class Guest(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    passport_number = models.CharField(max_length=50, verbose_name='Документ')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    nationality = models.CharField(max_length=50, default='Россия', verbose_name='Гражданство')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Гость'
        verbose_name_plural = 'Гости'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    def get_full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)


class Booking(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.PROTECT, related_name='bookings', verbose_name='Гость')
    capsule = models.ForeignKey(Capsule, on_delete=models.PROTECT, related_name='bookings', verbose_name='Капсула')
    check_in = models.DateTimeField(verbose_name='Дата заезда')
    check_out = models.DateTimeField(verbose_name='Дата выезда')
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='confirmed', verbose_name='Статус')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='reception', verbose_name='Источник')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cash', verbose_name='Способ оплаты')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Сумма (руб.)')
    is_paid = models.BooleanField(default=False, verbose_name='Оплачено')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Extra services
    has_towel = models.BooleanField(default=False, verbose_name='Полотенце')
    has_slippers = models.BooleanField(default=False, verbose_name='Тапочки')
    has_hygiene = models.BooleanField(default=False, verbose_name='Гигиенический набор')
    has_meal = models.BooleanField(default=False, verbose_name='Питание')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-created_at']

    def __str__(self):
        return f'Бронь #{self.pk} — {self.guest} — Капсула {self.capsule.number}'

    def get_duration_minutes(self):
        """Фактическая продолжительность в минутах, минимум 60 (1 час)."""
        delta = self.check_out - self.check_in
        return max(60, int(delta.total_seconds() / 60))

    def get_duration_hours(self):
        """Для отображения — дробное кол-во часов."""
        return round(self.get_duration_minutes() / 60, 2)

    def get_duration_display(self):
        """Человекочитаемая строка: 'X ч Y мин'."""
        total_min = self.get_duration_minutes()
        h = total_min // 60
        m = total_min % 60
        if m:
            return f'{h} ч {m} мин'
        return f'{h} ч'

    def calculate_total(self):
        """Стоимость = цена/мин × минуты + услуги."""
        minutes = self.get_duration_minutes()
        price_per_minute = self.capsule.price_per_hour / 60
        base = round(price_per_minute * minutes, 2)
        extras = 0
        if self.has_towel:    extras += 150
        if self.has_slippers: extras += 100
        if self.has_hygiene:  extras += 200
        if self.has_meal:     extras += 350
        return round(base + extras, 2)

    def get_status_color(self):
        colors = {
            'confirmed': 'warning',
            'checked_in': 'success',
            'checked_out': 'secondary',
            'cancelled': 'danger',
        }
        return colors.get(self.status, 'secondary')
