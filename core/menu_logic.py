import pandas as pd
import numpy as np
from collections import Counter
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
from django.db.models import Count, Q

class MenuPlanner:
    """Класс для анализа предпочтений и составления меню"""

    def __init__(self, guests, all_dishes):
        self.guests = guests
        self.all_dishes = all_dishes
        self.dishes_df = self._create_dishes_dataframe()

    def _create_dishes_dataframe(self) -> pd.DataFrame:
        """Создание DataFrame со всеми блюдами"""
        dishes_data = []
        for dish in self.all_dishes:
            dishes_data.append({
                'dish_id': dish.id,
                'name': dish.name,
                'dish_type': dish.dish_type.name if dish.dish_type else '',
                'cooking_time': dish.cooking_time,
                'difficulty': dish.difficulty,
                'popularity': dish.popularity_score,
                'ingredients_count': dish.ingredients_list.count()
            })
        return pd.DataFrame(dishes_data)

    def find_dish_intersections(self, min_common: int = 2) -> pd.DataFrame:
        """
        Находит блюда, которые нравятся нескольким гостям

        Args:
            min_common: минимальное количество гостей, которым должно нравиться блюдо

        Returns:
            DataFrame с блюдами и количеством гостей, которым они нравятся
        """
        dish_guests_map = {}

        # Собираем информацию о том, какие блюда нравятся каким гостям
        for guest in self.guests:
            for dish in guest.favorite_dishes.all():
                if dish.id not in dish_guests_map:
                    dish_guests_map[dish.id] = {
                        'dish': dish,
                        'guest_count': 0,
                        'guests': []
                    }
                dish_guests_map[dish.id]['guest_count'] += 1
                dish_guests_map[dish.id]['guests'].append(guest.name)

        # Создаем DataFrame
        intersections_data = []
        for dish_id, data in dish_guests_map.items():
            if data['guest_count'] >= min_common:
                dish = data['dish']
                intersections_data.append({
                    'dish_id': dish.id,
                    'name': dish.name,
                    'dish_type': dish.dish_type.name if dish.dish_type else '',
                    'guest_count': data['guest_count'],
                    'guests': ', '.join(data['guests']),
                    'cooking_time': dish.cooking_time,
                    'difficulty': dish.difficulty
                })

        df = pd.DataFrame(intersections_data)
        if not df.empty:
            df = df.sort_values('guest_count', ascending=False)

        return df

    def suggest_menu(
            self,
            max_dishes: int = 8,
            max_cooking_time: int = 180,
            balance_types: bool = True
    ) -> List[Dict]:
        """
        Предлагает меню на основе анализа пересечений

        Args:
            max_dishes: максимальное количество блюд в меню
            max_cooking_time: максимальное общее время приготовления
            balance_types: сбалансировать типы блюд

        Returns:
            Список рекомендованных блюд
        """
        # Получаем пересечения
        intersections_df = self.find_dish_intersections(min_common=1)

        if intersections_df.empty:
            # Если нет пересечений, используем популярные блюда
            suggestions = self.all_dishes.order_by('-popularity_score')[:max_dishes]
            return [
                {
                    'dish': dish,
                    'reason': 'Популярное блюдо',
                    'score': dish.popularity_score
                }
                for dish in suggestions
            ]

        # Сортируем по количеству гостей и популярности
        intersections_df['score'] = (
                intersections_df['guest_count'] * 0.7 +
                intersections_df['cooking_time'].apply(lambda x: 1 - (x / max_cooking_time)) * 0.3
        )

        suggestions = []
        selected_types = set()
        total_time = 0

        # Отбираем блюда
        for _, row in intersections_df.iterrows():
            if len(suggestions) >= max_dishes:
                break

            dish = next((d for d in self.all_dishes if d.id == row['dish_id']), None)
            if not dish:
                continue

            # Проверяем время приготовления
            if total_time + dish.cooking_time > max_cooking_time:
                continue

            # Балансируем типы блюд
            if balance_types:
                dish_type = dish.dish_type.name if dish.dish_type else 'other'
                if dish_type in selected_types:
                    continue

            suggestions.append({
                'dish': dish,
                'reason': f'Нравится {int(row["guest_count"])} гостям',
                'score': row['score'],
                'guests': row['guests']
            })

            if dish.dish_type:
                selected_types.add(dish.dish_type.name)
            total_time += dish.cooking_time

        # Сортируем по убыванию оценки
        suggestions.sort(key=lambda x: x['score'], reverse=True)

        return suggestions

    def calculate_shopping_list(
            self,
            selected_dishes: List,
            guests_count: int
    ) -> Dict[str, List]:
        """
        Рассчитывает список продуктов для закупки

        Args:
            selected_dishes: список выбранных блюд
            guests_count: количество гостей

        Returns:
            Словарь с категоризированным списком продуктов
        """
        shopping_dict = {}
        total_cost = 0

        for dish_data in selected_dishes:
            dish = dish_data['dish']
            servings = dish_data.get('servings', guests_count)

            for dish_ingredient in dish.ingredients_list.all():
                ingredient = dish_ingredient.ingredient
                quantity_needed = dish_ingredient.quantity * servings

                if ingredient.id not in shopping_dict:
                    shopping_dict[ingredient.id] = {
                        'ingredient': ingredient,
                        'quantity': 0,
                        'unit': ingredient.unit,
                        'estimated_cost': 0,
                        'dishes': []
                    }

                shopping_dict[ingredient.id]['quantity'] += quantity_needed
                shopping_dict[ingredient.id]['dishes'].append(dish.name)

                # Расчет стоимости
                if ingredient.average_price:
                    cost = (quantity_needed / 1000) * float(ingredient.average_price)  # для грамм/кг
                    shopping_dict[ingredient.id]['estimated_cost'] += cost
                    total_cost += cost

        # Преобразуем в список и сортируем
        shopping_list = list(shopping_dict.values())
        shopping_list.sort(key=lambda x: x['ingredient'].category or '')

        return {
            'items': shopping_list,
            'total_cost': total_cost,
            'guests_count': guests_count
        }

    def create_visualizations(self, selected_dishes: List) -> Dict[str, str]:
        """
        Создает визуализации для меню

        Args:
            selected_dishes: список выбранных блюд

        Returns:
            Словарь с base64-изображениями графиков
        """
        visualizations = {}

        if not selected_dishes:
            return visualizations

        # 1. График распределения типов блюд
        dish_types = []
        for dish_data in selected_dishes:
            dish_type = dish_data['dish'].dish_type
            dish_types.append(dish_type.name if dish_type else 'Другое')

        type_counts = Counter(dish_types)

        plt.figure(figsize=(10, 6))
        plt.subplot(2, 2, 1)
        plt.pie(
            type_counts.values(),
            labels=type_counts.keys(),
            autopct='%1.1f%%',
            colors=sns.color_palette('pastel')
        )
        plt.title('Распределение типов блюд')

        # 2. График сложности приготовления
        difficulties = [dish_data['dish'].difficulty for dish_data in selected_dishes]
        difficulty_counts = Counter(difficulties)

        plt.subplot(2, 2, 2)
        sns.barplot(
            x=list(difficulty_counts.keys()),
            y=list(difficulty_counts.values()),
            palette='viridis'
        )
        plt.title('Сложность приготовления')
        plt.xlabel('Уровень сложности')
        plt.ylabel('Количество блюд')

        # 3. График времени приготовления
        cooking_times = [dish_data['dish'].cooking_time for dish_data in selected_dishes]

        plt.subplot(2, 2, 3)
        plt.bar(range(len(cooking_times)), cooking_times)
        plt.title('Время приготовления по блюдам')
        plt.xlabel('Блюдо')
        plt.ylabel('Время (мин)')
        plt.xticks([])

        # 4. График популярности
        popularity_scores = [dish_data['dish'].popularity_score for dish_data in selected_dishes]
        dish_names = [dish_data['dish'].name[:15] + '...' for dish_data in selected_dishes]

        plt.subplot(2, 2, 4)
        plt.barh(dish_names, popularity_scores)
        plt.title('Популярность блюд')
        plt.xlabel('Оценка популярности')

        plt.tight_layout()

        # Сохраняем в base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()

        visualizations['menu_analysis'] = base64.b64encode(image_png).decode('utf-8')
        plt.close()

        return visualizations