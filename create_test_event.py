import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'holiday_menu.settings')
django.setup()

from core.models import HolidayEvent, Guest, Dish
import datetime

# Создаем тестовое мероприятие
event = HolidayEvent.objects.create(
    name="Тестовый праздник",
    event_date=datetime.date.today(),
    number_of_guests=3
)

# Добавляем гостей
guests = Guest.objects.all()[:3]
for guest in guests:
    event.guests.add(guest)
    
    # Добавляем любимые блюда гостям
    dishes = Dish.objects.all()[:2]  # Каждому гостю по 2 любимых блюда
    guest.favorite_dishes.add(*dishes)

event.save()

print(f"✅ Создано мероприятие: {event.name} (ID: {event.id})")
print(f"   Гостей: {event.guests.count()}")
print(f"   URL меню: http://127.0.0.1:8000/event/{event.id}/menu/")
print(f"   URL покупок: http://127.0.0.1:8000/event/{event.id}/shopping/")

# Проверяем предпочтения
print("\n👥 Предпочтения гостей:")
for guest in event.guests.all():
    print(f"  {guest.name}: {guest.favorite_dishes.count()} блюд")
