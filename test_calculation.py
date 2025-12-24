import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'holiday_menu.settings')
django.setup()

from core.models import Dish, Ingredient

def calculate_item_cost(quantity, unit, price_per_unit):
    """Правильный расчет стоимости товара"""
    if not price_per_unit:
        return 0
    
    if unit == 'g':
        return (quantity / 1000) * price_per_unit
    elif unit == 'kg':
        return quantity * price_per_unit
    elif unit == 'pcs':
        return quantity * price_per_unit
    elif unit == 'l':
        return quantity * price_per_unit
    elif unit == 'ml':
        return (quantity / 1000) * price_per_unit
    else:
        return (quantity / 1000) * price_per_unit

print("=== ТЕСТ РАСЧЕТА СТОИМОСТИ ===")
print("Пример: Оливье на 10 гостей")
print("-" * 40)

olivye = Dish.objects.get(name='Оливье')
total = 0

for di in olivye.ingredients_list.all():
    ingredient = di.ingredient
    quantity_for_10 = di.quantity * 10  # на 10 гостей
    price = float(ingredient.average_price or 0)
    
    cost = calculate_item_cost(quantity_for_10, ingredient.unit, price)
    total += cost
    
    print(f"{ingredient.name}:")
    print(f"  Количество: {di.quantity}g на 1 гостя → {quantity_for_10}g на 10 гостей")
    print(f"  Цена: {price} ₽/{'кг' if ingredient.unit == 'g' else ingredient.unit}")
    print(f"  Стоимость: {cost:.2f} ₽")
    print()

print("-" * 40)
print(f"Итого за Оливье на 10 гостей: {total:.2f} ₽")
print(f"На одного гостя: {total/10:.2f} ₽")

# Теперь посчитаем для нескольких блюд
print("\n=== РАСЧЕТ ДЛЯ НЕСКОЛЬКИХ БЛЮД ===")
dishes_to_check = ['Оливье', 'Сельдь под шубой', 'Шашлык из свинины']
total_all = 0

for dish_name in dishes_to_check:
    try:
        dish = Dish.objects.get(name=dish_name)
        dish_total = 0
        
        for di in dish.ingredients_list.all():
            quantity_for_10 = di.quantity * 10
            price = float(di.ingredient.average_price or 0)
            cost = calculate_item_cost(quantity_for_10, di.ingredient.unit, price)
            dish_total += cost
        
        total_all += dish_total
        print(f"{dish_name}: {dish_total:.2f} ₽ на 10 гостей")
        
    except Dish.DoesNotExist:
        print(f"{dish_name}: не найдено")

print(f"\nОбщая стоимость 3 блюд на 10 гостей: {total_all:.2f} ₽")
print(f"На гостя: {total_all/10:.2f} ₽")
print(f"\n💡 Это реалистичная стоимость! (а не 556,230 ₽)")
