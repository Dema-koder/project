import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'holiday_menu.settings')
django.setup()

from core.models import Ingredient

# Реалистичные цены (в рублях за единицу измерения)
realistic_prices = {
    # Овощи (цена за кг)
    'Картофель': 60,
    'Морковь': 80,
    'Лук репчатый': 50,
    'Огурцы': 120,
    'Помидоры': 150,
    'Капуста': 40,
    'Свекла': 70,
    'Чеснок': 300,
    'Зелень': 300,  # за кг, хотя обычно за пучок
    
    # Мясо (цена за кг)
    'Свинина': 400,
    'Говядина': 500,
    'Курица': 350,
    'Сельдь': 300,
    
    # Молочные (цена за кг/литр)
    'Майонез': 200,
    'Сметана': 180,
    'Сыр': 600,
    'Молоко': 90,
    'Йогурт': 150,
    
    # Бакалея
    'Яйца': 10,  # за штуку
    'Рис': 120,  # за кг
    'Мука': 80,  # за кг
    'Сахар': 90,  # за кг
    'Соль': 40,  # за кг
    'Масло растительное': 120,  # за литр
    
    # Прочее
    'Перец черный': 0.005,  # за грамм (5 руб/кг)
    'Крабовые палочки': 400,  # за кг
    'Кукуруза': 100,  # за банку
    'Лимон': 50,  # за штуку
    'Авокадо': 200,  # за штуку
}

print("Исправление цен в базе данных...")
updated = 0

for ingredient in Ingredient.objects.all():
    if ingredient.name in realistic_prices:
        old_price = ingredient.average_price
        new_price = realistic_prices[ingredient.name]
        
        if old_price != new_price:
            ingredient.average_price = new_price
            ingredient.save()
            print(f"  {ingredient.name}: {old_price} → {new_price} ₽")
            updated += 1

print(f"\n✅ Обновлено {updated} ингредиентов")
print("\nПример расчета для 10 гостей:")

# Пример расчета
from core.models import Dish, DishIngredient
olivye = Dish.objects.get(name='Оливье')
total = 0
print(f"\n🍽️ Блюдо: {olivye.name} (на 10 гостей):")
for di in olivye.ingredients_list.all():
    quantity = di.quantity * 10  # на 10 гостей
    price = float(di.ingredient.average_price or 0)
    
    # Конвертация единиц
    if di.ingredient.unit == 'g':
        cost = (quantity / 1000) * price
    elif di.ingredient.unit == 'pcs':
        cost = quantity * price
    else:
        cost = quantity * price
    
    total += cost
    print(f"  {di.ingredient.name}: {quantity}{di.ingredient.unit} = {cost:.2f} ₽")

print(f"  ИТОГО: {total:.2f} ₽")
print(f"  На гостя: {total/10:.2f} ₽")
