# GettSleep PMS — Информационная система управления хостелом

## Быстрый старт

### 1. Установка Python и Django

Убедитесь, что у вас установлен Python 3.10+:
```
python --version
```

Установите зависимости:
```
pip install -r requirements.txt
```

### 2. Инициализация базы данных

```
python manage.py migrate
```

### 3. Загрузка тестовых данных (необязательно)

```
python manage.py seed_data
```

Это создаст пользователей, капсулы и тестовые бронирования.

### 4. Создание суперпользователя (если не использовали seed_data)

```
python manage.py createsuperuser
```

### 5. Запуск сервера

```
python manage.py runserver
```

Откройте браузер: **http://127.0.0.1:8000/**

---

## Учётные записи (после seed_data)

| Логин        | Пароль       | Роль                   |
|--------------|--------------|------------------------|
| admin        | admin123     | Суперпользователь      |
| manager      | manager123   | Менеджер               |
| reception1   | reception123 | Администратор ресепшена|
| reception2   | reception123 | Администратор ресепшена|
| maid1        | maid123      | Горничная              |
| maid2        | maid123      | Горничная              |

---

## Структура проекта

```
gettsleep/
├── manage.py
├── requirements.txt
├── README.md
├── gettsleep_pms/          # Настройки проекта
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── core/               # Профили, аудит, дашборд
│   ├── bookings/           # Бронирования и гости
│   ├── rooms/              # Капсулы (номерной фонд)
│   ├── cleaning/           # Задачи уборки
│   └── reports/            # Аналитика
├── templates/              # HTML-шаблоны
│   ├── base.html
│   ├── dashboard.html
│   ├── registration/
│   ├── bookings/
│   ├── rooms/
│   ├── cleaning/
│   └── reports/
└── static/                 # Статические файлы (CSS, JS)
```

Установите драйвер: `pip install psycopg2-binary`
