from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
import json

def generate_shopping_list_debug(request, event_id):
    """Версия для отладки расчета"""
    from .models import HolidayEvent, Dish
    from collections import Counter
    import json
    
    event = HolidayEvent.objects.get(id=event_id)
    
    # Собираем блюда
    all_dishes = []
    for guest in event.guests.all():
        all_dishes.extend(list(guest.favorite_dishes.all()))
    
    if not all_dishes:
        all_dishes = list(Dish.objects.all()[:2])
    
    dish_counter = Counter(all_dishes)
    popular_dishes = [dish for dish, _ in dish_counter.most_common(3)]
    
    # Детальный расчет
    debug_info = {
        'event': {
            'name': event.name,
            'guests': event.number_of_guests,
        },
        'dishes': [],
        'calculation_steps': [],
        'total': 0
    }
    
    total_cost = 0
    
    for dish in popular_dishes:
        dish_info = {
            'name': dish.name,
            'ingredients': [],
            'dish_total': 0
        }
        
        for di in dish.ingredients_list.all():
            ingredient = di.ingredient
            
            # Исходные данные
            quantity_per_guest = di.quantity
            unit = ingredient.unit
            price = float(ingredient.average_price or 0)
            
            # Расчет для всех гостей
            total_quantity = quantity_per_guest * event.number_of_guests
            
            # Расчет стоимости
            if unit == 'g':
                # граммы → килограммы
                cost = (total_quantity / 1000) * price
                calculation = f"({total_quantity}g / 1000) × {price}₽/кг = {cost:.2f}₽"
            elif unit == 'kg':
                cost = total_quantity * price
                calculation = f"{total_quantity}кг × {price}₽/кг = {cost:.2f}₽"
            elif unit == 'pcs':
                cost = total_quantity * price
                calculation = f"{total_quantity}шт × {price}₽/шт = {cost:.2f}₽"
            elif unit == 'l':
                cost = total_quantity * price
                calculation = f"{total_quantity}л × {price}₽/л = {cost:.2f}₽"
            elif unit == 'ml':
                cost = (total_quantity / 1000) * price
                calculation = f"({total_quantity}мл / 1000) × {price}₽/л = {cost:.2f}₽"
            else:
                cost = total_quantity * price
                calculation = f"{total_quantity}{unit} × {price}₽ = {cost:.2f}₽"
            
            ingredient_info = {
                'name': ingredient.name,
                'quantity_per_guest': quantity_per_guest,
                'unit': unit,
                'price_per_unit': price,
                'total_quantity': total_quantity,
                'cost': cost,
                'calculation': calculation
            }
            
            dish_info['ingredients'].append(ingredient_info)
            dish_info['dish_total'] += cost
            total_cost += cost
        
        debug_info['dishes'].append(dish_info)
    
    debug_info['total'] = total_cost
    
    # Формируем HTML для отображения
    html = f"""
    <html>
    <head>
        <title>Отладка расчета</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .event {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .dish {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .ingredient {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #2196f3; }}
            .total {{ background: #4caf50; color: white; padding: 20px; border-radius: 5px; font-size: 24px; text-align: center; }}
            .warning {{ background: #ffeb3b; padding: 10px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h1>🔧 Отладка расчета стоимости</h1>
        
        <div class="event">
            <h2>Мероприятие: {debug_info['event']['name']}</h2>
            <p>Количество гостей: {debug_info['event']['guests']}</p>
        </div>
    """
    
    for dish_info in debug_info['dishes']:
        html += f"""
        <div class="dish">
            <h3>🍽️ Блюдо: {dish_info['name']}</h3>
            <p>Общая стоимость блюда: <strong>{dish_info['dish_total']:.2f} ₽</strong></p>
        """
        
        for ing in dish_info['ingredients']:
            html += f"""
            <div class="ingredient">
                <strong>{ing['name']}</strong><br>
                <small>
                    На гостя: {ing['quantity_per_guest']}{ing['unit']}<br>
                    На всех гостей: {ing['total_quantity']}{ing['unit']}<br>
                    Цена: {ing['price_per_unit']} ₽/{'кг' if ing['unit'] == 'g' else ing['unit']}<br>
                    Расчет: {ing['calculation']}
                </small>
            </div>
            """
        
        html += "</div>"
    
    html += f"""
        <div class="total">
            <h2>Итоговая стоимость: {debug_info['total']:.2f} ₽</h2>
            <p>На одного гостя: {debug_info['total'] / debug_info['event']['guests']:.2f} ₽</p>
        </div>
        
        <div class="warning">
            <h3>⚠️ Если цена все еще высокая:</h3>
            <ol>
                <li>Проверьте quantity в DishIngredient - возможно, там указано количество на 100 гостей</li>
                <li>Проверьте unit - возможно, 'g' означает не граммы, а что-то другое</li>
                <li>Проверьте average_price - возможно, цена указана не за единицу, а за 100 единиц</li>
            </ol>
        </div>
        
        <h3>📊 JSON данных для анализа:</h3>
        <pre>{json.dumps(debug_info, indent=2, ensure_ascii=False)}</pre>
    </body>
    </html>
    """
    
    return HttpResponse(html)
