from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Avg, Count
from collections import Counter
from .models import Dish, HolidayEvent, Guest, DishType, ShoppingList, ShoppingItem, Ingredient, DishIngredient
import datetime

def index(request):
    return render(request, 'core/index.html')

def create_event(request):
    if request.method == 'POST':
        try:
            event_name = request.POST.get('event_name')
            event_date = request.POST.get('event_date')
            guests_count = request.POST.get('guests_count')
            
            if not all([event_name, event_date, guests_count]):
                return HttpResponse("Все поля обязательны", status=400)
            
            date_obj = datetime.datetime.strptime(event_date, '%Y-%m-%d').date()
            
            event = HolidayEvent.objects.create(
                name=event_name,
                event_date=date_obj,
                number_of_guests=int(guests_count)
            )
            return redirect('add_guests', event_id=event.id)
            
        except ValueError as e:
            return HttpResponse(f"Ошибка в данных: {e}", status=400)
    
    context = {'today': timezone.now().date()}
    return render(request, 'core/create_event.html', context)

def add_guests(request, event_id):
    event = get_object_or_404(HolidayEvent, id=event_id)
    dishes = Dish.objects.all()
    
    if request.method == 'POST':
        guests_count = event.number_of_guests
        
        for i in range(1, guests_count + 1):
            guest_name = request.POST.get(f'guest_{i}_name')
            dish_ids = request.POST.getlist(f'guest_{i}_dishes')
            
            if guest_name:
                guest, created = Guest.objects.get_or_create(
                    name=guest_name,
                    defaults={'email': ''}
                )
                
                event.guests.add(guest)
                
                if dish_ids:
                    favorite_dishes = Dish.objects.filter(id__in=dish_ids)
                    guest.favorite_dishes.add(*favorite_dishes)
        
        event.save()
        return redirect('generate_menu', event_id=event.id)
    
    guest_range = range(1, int(event.number_of_guests) + 1)
    
    return render(request, 'core/add_guests.html', {
        'event': event,
        'dishes': dishes,
        'guest_range': guest_range
    })

def dish_list(request):
    dishes = Dish.objects.all().select_related('dish_type')
    
    dish_types_count = DishType.objects.count()
    avg_cooking_time = dishes.aggregate(Avg('cooking_time'))['cooking_time__avg'] or 0
    easy_dishes = dishes.filter(difficulty='easy').count()
    
    context = {
        'dishes': dishes,
        'dish_types_count': dish_types_count,
        'avg_cooking_time': avg_cooking_time,
        'easy_dishes': easy_dishes,
    }
    
    return render(request, 'core/dish_list.html', context)

def generate_menu(request, event_id):
    """Генерация меню на основе предпочтений гостей"""
    event = get_object_or_404(HolidayEvent, id=event_id)
    guests = event.guests.all()
    
    if not guests.exists():
        return HttpResponse("Нет данных о гостях", status=400)
    
    all_favorite_dishes = []
    for guest in guests:
        all_favorite_dishes.extend(list(guest.favorite_dishes.all()))
    
    if not all_favorite_dishes:
        return HttpResponse("Гости не выбрали любимые блюда", status=400)
    
    dish_counter = Counter(all_favorite_dishes)
    popular_dishes = dish_counter.most_common(6)
    
    type_distribution = Counter([
        d.dish_type.name if d.dish_type else 'Разное' 
        for d, _ in popular_dishes
    ]).most_common()
    
    context = {
        'event': event,
        'popular_dishes': popular_dishes,
        'type_distribution': type_distribution,
        'guests_count': guests.count(),
    }
    
    return render(request, 'core/generate_menu.html', context)

def calculate_item_cost(quantity, unit, price_per_unit):
    """Правильный расчет стоимости товара"""
    if not price_per_unit:
        return 0
    
    # Конвертируем количество в единицы цены
    if unit == 'g':  # цена за кг, количество в граммах
        return (quantity / 1000) * price_per_unit
    elif unit == 'kg':  # цена за кг, количество в кг
        return quantity * price_per_unit
    elif unit == 'ml':  # цена за литр, количество в мл
        return (quantity / 1000) * price_per_unit
    elif unit == 'l':  # цена за литр, количество в литрах
        return quantity * price_per_unit
    elif unit == 'pcs':  # цена за штуку
        return quantity * price_per_unit
    elif unit == 'tbsp':  # столовая ложка ≈ 15г
        return (quantity * 0.015 / 1000) * price_per_unit
    elif unit == 'tsp':  # чайная ложка ≈ 5г
        return (quantity * 0.005 / 1000) * price_per_unit
    else:
        # По умолчанию считаем, что цена за кг
        return (quantity / 1000) * price_per_unit

def generate_shopping_list(request, event_id):
    """Формирование списка покупок для меню - РЕАЛИСТИЧНЫЙ РАСЧЕТ"""
    event = get_object_or_404(HolidayEvent, id=event_id)
    guests = event.guests.all()
    
    # Получаем выбранные блюда
    all_favorite_dishes = []
    for guest in guests:
        all_favorite_dishes.extend(list(guest.favorite_dishes.all()))
    
    if not all_favorite_dishes:
        all_favorite_dishes = list(Dish.objects.all()[:3])
        if not all_favorite_dishes:
            return HttpResponse("Нет данных о блюдах", status=400)
    
    # Находим популярные блюда
    dish_counter = Counter(all_favorite_dishes)
    popular_dishes = [dish for dish, _ in dish_counter.most_common(5)]
    
    # Считаем ингредиенты
    shopping_dict = {}
    total_cost = 0
    
    for dish in popular_dishes:
        for dish_ingredient in dish.ingredients_list.all():
            ingredient = dish_ingredient.ingredient
            quantity_needed = dish_ingredient.quantity * event.number_of_guests
            
            if ingredient.id not in shopping_dict:
                shopping_dict[ingredient.id] = {
                    'ingredient': ingredient,
                    'quantity': 0,
                    'unit': ingredient.unit,
                    'dishes': [],
                    'estimated_cost': 0
                }
            
            shopping_dict[ingredient.id]['quantity'] += quantity_needed
            shopping_dict[ingredient.id]['dishes'].append(dish.name)
            
            # ПРАВИЛЬНЫЙ РАСЧЕТ СТОИМОСТИ
            price_per_unit = float(ingredient.average_price or 0)
            item_cost = calculate_item_cost(quantity_needed, ingredient.unit, price_per_unit)
            
            shopping_dict[ingredient.id]['estimated_cost'] += item_cost
            total_cost += item_cost
    
    if not shopping_dict:
        return render(request, 'core/shopping_list_empty.html', {
            'event': event,
            'popular_dishes': popular_dishes,
        })
    
    # Сортируем по категориям
    categories = {}
    for item in shopping_dict.values():
        category = item['ingredient'].category or 'Другое'
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    # Сохраняем в базе
    shopping_list, created = ShoppingList.objects.get_or_create(event=event)
    shopping_list.total_cost = total_cost
    shopping_list.save()
    
    shopping_list.items.all().delete()
    
    for item_data in shopping_dict.values():
        ShoppingItem.objects.create(
            shopping_list=shopping_list,
            ingredient=item_data['ingredient'],
            quantity_needed=item_data['quantity'],
            estimated_cost=item_data.get('estimated_cost', 0)
        )
    
    per_guest_cost = total_cost / event.number_of_guests if event.number_of_guests > 0 else 0
    
    context = {
        'event': event,
        'categories': categories,
        'total_cost': total_cost,
        'per_guest_cost': per_guest_cost,
        'popular_dishes': popular_dishes,
        'shopping_list': shopping_list,
        'guests_count': event.number_of_guests,
    }
    
    return render(request, 'core/shopping_list.html', context)

def show_event(request, event_id):
    """Отладочная страница для просмотра мероприятия"""
    event = get_object_or_404(HolidayEvent, id=event_id)
    guests = event.guests.all()
    
    guests_with_dishes = sum(1 for guest in guests if guest.favorite_dishes.exists())
    total_dishes = sum(guest.favorite_dishes.count() for guest in guests)
    
    return render(request, 'core/show_event.html', {
        'event': event,
        'guests': guests,
        'guests_with_dishes': guests_with_dishes,
        'total_dishes': total_dishes,
    })

def edit_guest(request, event_id, guest_id):
    """Редактирование предпочтений гостя"""
    event = get_object_or_404(HolidayEvent, id=event_id)
    guest = get_object_or_404(Guest, id=guest_id)
    dishes = Dish.objects.all().select_related('dish_type')
    dish_types = DishType.objects.all()
    
    if request.method == 'POST':
        guest_name = request.POST.get('guest_name')
        if guest_name:
            guest.name = guest_name
            guest.save()
        
        dish_ids = request.POST.getlist('favorite_dishes')
        guest.favorite_dishes.clear()
        if dish_ids:
            favorite_dishes = Dish.objects.filter(id__in=dish_ids)
            guest.favorite_dishes.add(*favorite_dishes)
        
        return redirect('show_event', event_id=event_id)
    
    context = {
        'event': event,
        'guest': guest,
        'dishes': dishes,
        'dish_types': dish_types,
        'selected_dishes': list(guest.favorite_dishes.values_list('id', flat=True))
    }
    
    return render(request, 'core/edit_guest.html', context)

def delete_guest(request, event_id, guest_id):
    """Удаление гостя из мероприятия"""
    event = get_object_or_404(HolidayEvent, id=event_id)
    guest = get_object_or_404(Guest, id=guest_id)
    
    if request.method == 'POST':
        event.guests.remove(guest)
        return redirect('show_event', event_id=event_id)
    
    return render(request, 'core/delete_guest.html', {
        'event': event,
        'guest': guest
    })
from .views_debug import generate_shopping_list_debug

def generate_shopping_list_debug(request, event_id):
    """Отладочная версия расчета стоимости"""
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponse
    from .models import HolidayEvent, Dish
    from collections import Counter
    import json
    
    event = get_object_or_404(HolidayEvent, id=event_id)
    
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
                cost = (total_quantity / 1000) * price
                calculation = f"({total_quantity}g / 1000) × {price}₽/кг"
            elif unit == 'kg':
                cost = total_quantity * price
                calculation = f"{total_quantity}кг × {price}₽/кг"
            elif unit == 'pcs':
                cost = total_quantity * price
                calculation = f"{total_quantity}шт × {price}₽/шт"
            elif unit == 'l':
                cost = total_quantity * price
                calculation = f"{total_quantity}л × {price}₽/л"
            elif unit == 'ml':
                cost = (total_quantity / 1000) * price
                calculation = f"({total_quantity}мл / 1000) × {price}₽/л"
            else:
                cost = total_quantity * price
                calculation = f"{total_quantity}{unit} × {price}₽"
            
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
    
    # Формируем HTML
    html = f"""
    <html>
    <head>
        <title>Отладка расчета стоимости</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .event {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .dish {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .ingredient {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #2196f3; }}
            .total {{ background: #4caf50; color: white; padding: 20px; border-radius: 5px; font-size: 24px; text-align: center; }}
            .warning {{ background: #ffeb3b; padding: 10px; border-radius: 5px; margin: 10px 0; }}
            table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>🔧 Отладка расчета стоимости</h1>
        
        <div class="event">
            <h2>Мероприятие: {debug_info['event']['name']}</h2>
            <p>Количество гостей: {debug_info['event']['guests']}</p>
        </div>
        
        <table>
            <tr>
                <th>Блюдо</th>
                <th>Стоимость</th>
                <th>На гостя</th>
            </tr>
    """
    
    for dish_info in debug_info['dishes']:
        cost_per_guest = dish_info['dish_total'] / event.number_of_guests if event.number_of_guests > 0 else 0
        html += f"""
            <tr>
                <td>{dish_info['name']}</td>
                <td>{dish_info['dish_total']:.2f} ₽</td>
                <td>{cost_per_guest:.2f} ₽</td>
            </tr>
        """
        
        # Детали по ингредиентам
        html += f"""
            <tr>
                <td colspan="3">
                    <details>
                        <summary>Показать ингредиенты</summary>
                        <table>
                            <tr>
                                <th>Ингредиент</th>
                                <th>На гостя</th>
                                <th>На всех</th>
                                <th>Цена</th>
                                <th>Расчет</th>
                                <th>Стоимость</th>
                            </tr>
        """
        
        for ing in dish_info['ingredients']:
            html += f"""
                            <tr>
                                <td>{ing['name']}</td>
                                <td>{ing['quantity_per_guest']}{ing['unit']}</td>
                                <td>{ing['total_quantity']}{ing['unit']}</td>
                                <td>{ing['price_per_unit']} ₽/{'кг' if ing['unit'] == 'g' else ing['unit']}</td>
                                <td><small>{ing['calculation']}</small></td>
                                <td>{ing['cost']:.2f} ₽</td>
                            </tr>
            """
        
        html += """
                        </table>
                    </details>
                </td>
            </tr>
        """
    
    html += f"""
        </table>
        
        <div class="total">
            <h2>Итоговая стоимость: {debug_info['total']:.2f} ₽</h2>
            <p>На одного гостя: {debug_info['total'] / debug_info['event']['guests']:.2f} ₽</p>
        </div>
        
        <div class="warning">
            <h3>⚠️ Если цена все еще высокая, проверьте:</h3>
            <ol>
                <li><strong>DishIngredient.quantity</strong> - должно быть количество НА ОДНОГО ГОСТЯ</li>
                <li><strong>Ingredient.average_price</strong> - цена за единицу (кг, шт, литр)</li>
                <li><strong>Ingredient.unit</strong> - единица измерения</li>
            </ol>
            
            <h4>Пример правильных данных:</h4>
            <ul>
                <li>Картофель: quantity=200 (грамм на гостя), price=60 (руб/кг), unit='g'</li>
                <li>Яйца: quantity=1 (штук на гостя), price=10 (руб/шт), unit='pcs'</li>
                <li>Масло: quantity=50 (грамм на гостя), price=120 (руб/л), unit='g'</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return HttpResponse(html)
