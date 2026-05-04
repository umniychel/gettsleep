from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.core.models import UserProfile
from apps.rooms.models import Capsule
from apps.bookings.models import Guest, Booking
from apps.cleaning.models import CleaningTask
from apps.guest.models import GuestUser
from django.utils import timezone
import datetime


class Command(BaseCommand):
    help = 'Заполнить базу данных тестовыми данными'

    def handle(self, *args, **kwargs):
        self.stdout.write('=== Создание персонала ===')

        def make_staff(username, password, first, last, role, superuser=False):
            if User.objects.filter(username=username).exists():
                return User.objects.get(username=username)
            email = f'{username}@gettsleep.ru'
            if superuser:
                u = User.objects.create_superuser(username, email, password)
            else:
                u = User.objects.create_user(username, email, password)
            u.first_name = first
            u.last_name = last
            u.is_staff = True
            u.save()
            UserProfile.objects.get_or_create(user=u, defaults={'role': role})
            return u

        make_staff('admin',      'admin123',     'Администратор', 'Системы',  'manager', superuser=True)
        make_staff('manager',    'manager123',   'Мария',         'Иванова',  'manager')
        make_staff('reception1', 'reception123', 'Алексей',       'Петров',   'admin')
        make_staff('reception2', 'reception123', 'Ольга',         'Сидорова', 'admin')
        make_staff('maid1',      'maid123',      'Татьяна',       'Козлова',  'maid')
        make_staff('maid2',      'maid123',      'Светлана',      'Новикова', 'maid')
        self.stdout.write('  Персонал создан.')

        # ── Тестовый гость ──────────────────────────────────────────
        self.stdout.write('=== Создание тестового гостя ===')
        if not User.objects.filter(username='guest').exists():
            gu = User.objects.create_user('guest', 'guest@mail.ru', 'guest123')
            gu.first_name = 'Иван'
            gu.last_name = 'Тестов'
            gu.save()
            GuestUser.objects.create(
                user=gu,
                phone='+7 900 000 00 00',
                passport_number='1234 567890',
                nationality='Россия',
            )
            self.stdout.write('  guest / guest123 — создан.')
        else:
            self.stdout.write('  guest — уже существует.')

        # ── Капсулы ──────────────────────────────────────────────────
        self.stdout.write('=== Создание капсул ===')
        capsules_data = [
            ('A01','single',1,600), ('A02','single',1,600), ('A03','double',1,900),
            ('A04','single',1,600), ('A05','single',1,600),
            ('B01','single',2,650), ('B02','single',2,650), ('B03','double',2,950),
            ('B04','family',2,1200),('B05','single',2,650),
            ('C01','single',3,700), ('C02','single',3,700), ('C03','single',3,700),
            ('C04','double',3,1000),('C05','family',3,1300),
        ]
        for num, ctype, floor, price in capsules_data:
            cap, created = Capsule.objects.get_or_create(
                number=num,
                defaults={'capsule_type':ctype,'floor':floor,'price_per_hour':price,'status':'free'}
            )
            if not created and cap.status not in ('cleaning',):
                cap.status = 'free'
                cap.save(update_fields=['status'])
        self.stdout.write(f'  {Capsule.objects.count()} капсул готово.')

        # ── Тестовые бронирования ────────────────────────────────────
        self.stdout.write('=== Создание бронирований ===')
        now = timezone.now()
        bookings_seed = [
            ('Иванов','Иван','Иванович','4510 123456','+7 999 111 22 33','Россия','A01',-2,8,'checked_in','reception'),
            ('Smith','John','','AA123456','+1 555 000 1234','США','A03',-1,6,'confirmed','booking'),
            ('Петрова','Анна','Сергеевна','7890 654321','+7 916 222 33 44','Россия','B01',-10,8,'checked_out','site'),
            ('Müller','Hans','','DE9876543','+49 30 1234567','Германия','B04',2,12,'confirmed','airbnb'),
            ('Ли','Вэй','','G12345678','+86 138 0000 0000','Китай','C01',-3,9,'checked_in','reception'),
        ]
        for ln,fn,mn,doc,phone,nat,cap_num,ci_off,dur,bstatus,src in bookings_seed:
            guest_obj, _ = Guest.objects.get_or_create(passport_number=doc, defaults={
                'last_name':ln,'first_name':fn,'middle_name':mn,'phone':phone,'nationality':nat,
            })
            capsule = Capsule.objects.get(number=cap_num)
            ci = now + datetime.timedelta(hours=ci_off)
            co = ci + datetime.timedelta(hours=dur)
            if not Booking.objects.filter(guest=guest_obj, capsule=capsule).exists():
                Booking.objects.create(
                    guest=guest_obj, capsule=capsule,
                    check_in=ci, check_out=co,
                    status=bstatus, source=src,
                    payment_method='card',
                    is_paid=bstatus in ('checked_in','checked_out'),
                    total_amount=capsule.price_per_hour * dur,
                )
                if bstatus == 'occupied':
                    capsule.status = 'occupied'; capsule.save(update_fields=['status'])
                elif bstatus == 'checked_in':
                    capsule.status = 'occupied'; capsule.save(update_fields=['status'])
                elif bstatus == 'confirmed':
                    capsule.status = 'booked';   capsule.save(update_fields=['status'])

        # ── Задачи уборки для checked_out ───────────────────────────
        self.stdout.write('=== Создание задач уборки ===')
        for b in Booking.objects.filter(status='checked_out'):
            cap = b.capsule
            if not CleaningTask.objects.filter(capsule=cap, status__in=['pending','in_progress']).exists():
                CleaningTask.objects.create(capsule=cap, cleaning_type='express', priority='high')
                cap.status = 'cleaning'
                cap.save(update_fields=['status'])

        self.stdout.write(self.style.SUCCESS(
            '\n✅ Готово!\n'
            '\n  Персонал (вход: /staff/login/):\n'
            '    admin       / admin123\n'
            '    manager     / manager123\n'
            '    reception1  / reception123\n'
            '    reception2  / reception123\n'
            '    maid1       / maid123\n'
            '    maid2       / maid123\n'
            '\n  Тестовый гость (вход: /guest/login/):\n'
            '    guest / guest123\n'
        ))
