from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Booking
from apps.rooms.models import Capsule


def recalc_capsule_status(capsule):
    """
    Пересчитывает и сохраняет статус капсулы на основе активных бронирований.
    Вызывается каждый раз при изменении брони.
    """
    now = timezone.now()

    # Есть ли кто-то заселён прямо сейчас?
    is_occupied = Booking.objects.filter(
        capsule=capsule,
        status='checked_in',
        check_in__lte=now,
        check_out__gte=now,
    ).exists()

    if is_occupied:
        new_status = 'occupied'
    else:
        # Есть ли подтверждённая бронь в будущем (в ближайшие 24ч)?
        soon = now + timezone.timedelta(hours=24)
        is_booked = Booking.objects.filter(
            capsule=capsule,
            status='confirmed',
            check_in__lte=soon,
            check_out__gte=now,
        ).exists()
        if is_booked:
            new_status = 'booked'
        elif capsule.status == 'cleaning':
            # Не трогаем — уборка управляется вручную
            new_status = 'cleaning'
        elif capsule.status in ('occupied', 'booked'):
            # Бронь завершилась — освобождаем
            new_status = 'free'
        else:
            new_status = capsule.status  # free / ready — не меняем

    if capsule.status != new_status:
        Capsule.objects.filter(pk=capsule.pk).update(status=new_status)


@receiver(post_save, sender=Booking)
def on_booking_save(sender, instance, **kwargs):
    """При любом изменении брони — пересчитываем статус капсулы."""
    recalc_capsule_status(instance.capsule)
