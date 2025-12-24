from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import pandas as pd

from core.models import Dish, Ingredient, HolidayEvent, Guest
from .serializers import (
    DishSerializer,
    IngredientSerializer,
    EventSerializer,
    GuestSerializer
)

class DishViewSet(viewsets.ModelViewSet):
    """API для блюд"""
    queryset = Dish.objects.all().select_related('dish_type')
    serializer_class = DishSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['dish_type', 'difficulty']
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['name', 'cooking_time', 'popularity_score']

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Статистика по блюдам"""
        dishes = self.get_queryset()

        # Используем pandas для анализа
        data = list(dishes.values(
            'name',
            'dish_type__name',
            'cooking_time',
            'difficulty',
            'popularity_score'
        ))

        if data:
            df = pd.DataFrame(data)

            stats = {
                'total_dishes': len(df),
                'avg_cooking_time': df['cooking_time'].mean(),
                'difficulty_distribution': df['difficulty'].value_counts().to_dict(),
                'type_distribution': df['dish_type__name'].value_counts().to_dict(),
                'top_popular': df.nlargest(5, 'popularity_score')[['name', 'popularity_score']].to_dict('records')
            }
        else:
            stats = {
                'total_dishes': 0,
                'avg_cooking_time': 0,
                'difficulty_distribution': {},
                'type_distribution': {},
                'top_popular': []
            }

        return Response(stats)

    @action(detail=False, methods=['post'])
    def find_intersections(self, request):
        """Поиск пересечений в предпочтениях"""
        dish_ids = request.data.get('dish_ids', [])

        if not dish_ids:
            return Response({'error': 'Нет данных о блюдах'}, status=400)

        # Получаем блюда
        dishes = Dish.objects.filter(id__in=dish_ids)

        # Используем pandas для анализа
        dish_data = []
        for dish in dishes:
            # Получаем гостей, которым нравится это блюдо
            guests = dish.favorited_by.all()
            dish_data.append({
                'dish_id': dish.id,
                'name': dish.name,
                'guest_count': guests.count(),
                'guests': [guest.name for guest in guests]
            })

        df = pd.DataFrame(dish_data)

        if not df.empty:
            # Сортируем по количеству гостей
            df = df.sort_values('guest_count', ascending=False)

            # Находим общих гостей
            all_guests = []
            for guests_list in df['guests']:
                all_guests.extend(guests_list)

            common_guests = []
            guest_counts = pd.Series(all_guests).value_counts()
            for guest, count in guest_counts.items():
                if count > 1:  # Гость встречается более чем в одном списке
                    common_guests.append({
                        'name': guest,
                        'common_dishes_count': count
                    })

        return Response({
            'dishes': df.to_dict('records'),
            'common_guests': common_guests if 'common_guests' in locals() else []
        })

class IngredientViewSet(viewsets.ModelViewSet):
    """API для ингредиентов"""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category']
    search_fields = ['name']

class EventViewSet(viewsets.ModelViewSet):
    """API для мероприятий"""
    queryset = HolidayEvent.objects.all().prefetch_related('guests', 'selected_dishes')
    serializer_class = EventSerializer

    @action(detail=True, methods=['get'])
    def shopping_list(self, request, pk=None):
        """Получение списка покупок для мероприятия"""
        event = self.get_object()

        try:
            shopping_list = event.shopping_list
            items = shopping_list.items.all()

            # Группируем по категориям
            categories = {}
            for item in items:
                category = item.ingredient.category or 'Другое'
                if category not in categories:
                    categories[category] = []
                categories[category].append({
                    'ingredient': item.ingredient.name,
                    'quantity': item.quantity_needed,
                    'unit': item.ingredient.unit,
                    'estimated_cost': float(item.estimated_cost) if item.estimated_cost else None
                })

            response_data = {
                'event': event.name,
                'total_cost': float(shopping_list.total_cost),
                'categories': categories
            }

        except ShoppingList.DoesNotExist:
            response_data = {
                'error': 'Список покупок не найден'
            }

        return Response(response_data)

class GuestViewSet(viewsets.ModelViewSet):
    """API для гостей"""
    queryset = Guest.objects.all().prefetch_related('favorite_dishes')
    serializer_class = GuestSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']