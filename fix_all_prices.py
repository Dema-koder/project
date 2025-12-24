import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'holiday_menu.settings')
django.setup()

from core.models import Ingredient

print("ИСПРАВЛЕНИЕ ВСЕХ ЦЕН В БАЗЕ ДАННЫХ")
print("=" * 50)

# Реалистичные цены в рублях
realistic_prices_rub = {
    # Овощи (цена за кг в рублях)
    'Картофель': 60,
    'Морковь': 80,
    'Лук': 50,
    'Лук репчатый': 50,
    'Огурцы': 120,
    'Помидоры': 150,
    'Свекла': 70,
    'Капуста': 40,
    'Чеснок': 300,
    'Зелень': 300,
    
    # Мясо (цена за кг)
    'Свинина': 400,
    'Говядина': 500,
    'Курица': 350,
    'Куриное филе': 400,
    'Сельдь': 300,
    
    # Молочные
    'Майонез': 200,
    'Сметана': 180,
    'Сыр': 600,
    'Йогурт': 150,
    
    # Бакалея
    'Яйца': 10,  # за штуку
    'Рис': 120,
    'Мука': 80,
    'Сахар': 90,
    'Соль': 40,
    'Масло': 120,
    'Масло растительное': 120,
    'Перец': 5,  # за 100г
    
    # Прочее
    'Крабовые палочки': 400,
    'Кукуруза': 100,
    'Лимон': 50,
    'Авокадо': 200,
    'Горошек': 120,
    'Уксус': 60,
}

# Исправляем ВСЕ цены
fixed_count = 0
for ingredient in Ingredient.objects.all():
    current_price = float(ingredient.average_price or 0)
    
    # Находим реалистичную цену
    realistic_price = None
    for key in realistic_prices_rub:
        if key.lower() in ingredient.name.lower():
            realistic_price = realistic_prices_rub[key]
            break
    
    # Если не нашли точного совпадения, используем категорию
    if realistic_price is None:
        if 'карто' in ingredient.name.lower() or 'морков' in ingredient.name.lower():
            realistic_price = 70
        elif 'лук' in ingredient.name.lower():
            realistic_price = 50
        elif 'мяс' in ingredient.name.lower():
            realistic_price = 450
        elif 'куриц' in ingredient.name.lower():
            realistic_price = 350
        elif 'яйц' in ingredient.name.lower():
            realistic_price = 10
        else:
            realistic_price = 100  # средняя цена по умолчанию
    
    # Если текущая цена в 100+ раз больше реалистичной, вероятно она в копейках
    if current_price > 0 and current_price / realistic_price > 100:
        print(f"⚠️ Подозрительная цена: {ingredient.name}")
        print(f"  Было: {current_price} ₽")
        print(f"  Стало: {realistic_price} ₽")
        print(f"  Коэффициент: {current_price / realistic_price:.0f}x")
    
    # Обновляем цену
    ingredient.average_price = realistic_price
    ingredient.save()
    fixed_count += 1

print(f"\n✅ Исправлено {fixed_count} ингредиентов")

# Покажем пример расчета
print("\n=== ПРИМЕР РАСЧЕТА ДЛЯ ОДНОГО ГОСТЯ ===")
from core.models import Dish
dish = Dish.objects.first()
if dish:
    total = 0
    for di in dish.ingredients_list.all():
        quantity = di.quantity
        price = float(di.ingredient.average_price or 0)
        
        if di.ingredient.unit == 'g':
            cost = (quantity / 1000) * price
        elif di.ingredient.unit == 'pcs':
            cost = quantity * price
        else:
            cost = quantity * price
            
        total += cost
    
    print(f"Блюдо '{dish.name}': {total:.2f} ₽ на одного гостя")
    
    if total > 500:
        print("⚠️ Все еще дорого, проверьте единицы измерения!")
