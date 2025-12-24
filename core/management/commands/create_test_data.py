from django.core.management.base import BaseCommand
from core.models import Dish, Ingredient, DishIngredient, DishType

class Command(BaseCommand):
    help = 'Создает тестовые данные для приложения'
    
    def handle(self, *args, **options):
        # Создаем ингредиенты если их нет
        ingredients_data = [
            # (Название, единица измерения, категория, средняя цена)
            ('Картофель', 'kg', 'Овощи', 60),
            ('Морковь', 'kg', 'Овощи', 80),
            ('Лук репчатый', 'kg', 'Овощи', 50),
            ('Майонез', 'kg', 'Соусы', 200),
            ('Куриное филе', 'kg', 'Мясо', 350),
            ('Говядина', 'kg', 'Мясо', 500),
            ('Помидоры', 'kg', 'Овощи', 150),
            ('Огурцы', 'kg', 'Овощи', 120),
            ('Сметана', 'kg', 'Молочные', 180),
            ('Яйца', 'pcs', 'Бакалея', 10),
            ('Мука', 'kg', 'Бакалея', 80),
            ('Сахар', 'kg', 'Бакалея', 90),
            ('Соль', 'kg', 'Бакалея', 40),
            ('Перец черный', 'g', 'Специи', 5),
            ('Масло растительное', 'l', 'Бакалея', 120),
        ]
        
        for name, unit, category, price in ingredients_data:
            Ingredient.objects.get_or_create(
                name=name,
                defaults={
                    'unit': unit,
                    'category': category,
                    'average_price': price
                }
            )
        
        self.stdout.write(f"Создано ингредиентов: {Ingredient.objects.count()}")
        
        # Создаем связи блюд с ингредиентами
        dishes_ingredients = {
            'Оливье': [
                ('Картофель', 300, 'вареный'),
                ('Морковь', 200, 'вареный'),
                ('Огурцы', 200, 'соленые'),
                ('Яйца', 4, 'вареные'),
                ('Майонез', 200, ''),
                ('Горошек', 150, 'консервированный'),
            ],
            'Сельдь под шубой': [
                ('Сельдь', 300, 'соленая'),
                ('Картофель', 400, 'вареный'),
                ('Морковь', 300, 'вареный'),
                ('Свекла', 300, 'вареный'),
                ('Лук репчатый', 100, ''),
                ('Майонез', 250, ''),
            ],
            'Крабовый салат': [
                ('Крабовые палочки', 300, ''),
                ('Кукуруза', 200, 'консервированная'),
                ('Яйца', 3, 'вареные'),
                ('Рис', 200, 'вареный'),
                ('Майонез', 150, ''),
                ('Зелень', 50, 'укроп'),
            ],
            'Шашлык': [
                ('Свинина', 1000, 'шейка'),
                ('Лук репчатый', 500, ''),
                ('Уксус', 100, 'винный'),
                ('Соль', 20, ''),
                ('Перец черный', 10, ''),
                ('Масло растительное', 50, ''),
            ],
            'Плов': [
                ('Рис', 500, ''),
                ('Говядина', 600, ''),
                ('Морковь', 300, ''),
                ('Лук репчатый', 300, ''),
                ('Масло растительное', 100, ''),
                ('Специи для плова', 50, ''),
            ],
        }
        
        for dish_name, ingredients_list in dishes_ingredients.items():
            try:
                dish = Dish.objects.get(name=dish_name)
                self.stdout.write(f"Найдено блюдо: {dish_name}")
                
                # Очищаем старые ингредиенты
                dish.ingredients_list.all().delete()
                
                # Добавляем новые ингредиенты
                for ing_name, quantity, notes in ingredients_list:
                    try:
                        ingredient = Ingredient.objects.get(name=ing_name)
                        DishIngredient.objects.create(
                            dish=dish,
                            ingredient=ingredient,
                            quantity=quantity,
                            notes=notes
                        )
                        self.stdout.write(f"  Добавлен: {ing_name} - {quantity}g")
                    except Ingredient.DoesNotExist:
                        # Создаем недостающий ингредиент
                        ingredient = Ingredient.objects.create(
                            name=ing_name,
                            unit='g',
                            category='Другое'
                        )
                        DishIngredient.objects.create(
                            dish=dish,
                            ingredient=ingredient,
                            quantity=quantity,
                            notes=notes
                        )
                        self.stdout.write(f"  Создан и добавлен: {ing_name}")
                
            except Dish.DoesNotExist:
                self.stdout.write(f"Блюдо не найдено: {dish_name}")
                continue
        
        self.stdout.write(self.style.SUCCESS('✅ Тестовые данные созданы успешно!'))
        
        # Показываем статистику
        for dish in Dish.objects.all():
            count = dish.ingredients_list.count()
            if count > 0:
                self.stdout.write(f"Блюдо '{dish.name}': {count} ингредиентов")
