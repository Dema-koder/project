from django.db import models
from django.core.validators import MinValueValidator
import uuid

class DishType(models.Model):
    """Тип блюда"""
    name = models.CharField(max_length=50, verbose_name="Название типа")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Тип блюда"
        verbose_name_plural = "Типы блюд"

    def __str__(self):
        return self.name

class Ingredient(models.Model):
    """Ингредиент/продукт"""
    UNIT_CHOICES = [
        ('g', 'грамм'),
        ('kg', 'килограмм'),
        ('ml', 'миллилитр'),
        ('l', 'литр'),
        ('pcs', 'штук'),
        ('tbsp', 'столовая ложка'),
        ('tsp', 'чайная ложка'),
    ]

    name = models.CharField(max_length=100, verbose_name="Название")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, verbose_name="Единица измерения")
    average_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Средняя цена"
    )
    category = models.CharField(max_length=50, blank=True, verbose_name="Категория")

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

class Dish(models.Model):
    """Блюдо"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Легко'),
        ('medium', 'Средне'),
        ('hard', 'Сложно'),
    ]

    name = models.CharField(max_length=200, verbose_name="Название блюда")
    description = models.TextField(verbose_name="Описание")
    dish_type = models.ForeignKey(
        DishType,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Тип блюда"
    )
    cooking_time = models.PositiveIntegerField(
        help_text="В минутах",
        verbose_name="Время приготовления"
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium',
        verbose_name="Сложность"
    )
    image = models.ImageField(
        upload_to='dishes/',
        null=True,
        blank=True,
        verbose_name="Изображение"
    )
    recipe = models.TextField(verbose_name="Рецепт")
    tags = models.CharField(max_length=200, blank=True, verbose_name="Теги")

    # Для анализа популярности
    popularity_score = models.FloatField(default=0.0, verbose_name="Популярность")

    class Meta:
        verbose_name = "Блюдо"
        verbose_name_plural = "Блюда"
        ordering = ['name']

    def __str__(self):
        return self.name

class DishIngredient(models.Model):
    """Ингредиенты для блюда с количеством"""
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='ingredients_list')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField(verbose_name="Количество")
    notes = models.CharField(max_length=100, blank=True, verbose_name="Примечания")

    class Meta:
        verbose_name = "Ингредиент блюда"
        verbose_name_plural = "Ингредиенты блюд"
        unique_together = ['dish', 'ingredient']

    def __str__(self):
        return f"{self.dish.name} - {self.ingredient.name}"

class Guest(models.Model):
    """Гость с предпочтениями"""
    name = models.CharField(max_length=100, verbose_name="Имя гостя")
    email = models.EmailField(blank=True, verbose_name="Email")
    preferences = models.TextField(blank=True, verbose_name="Предпочтения/аллергии")
    favorite_dishes = models.ManyToManyField(
        Dish,
        blank=True,
        related_name='favorited_by',
        verbose_name="Любимые блюда"
    )

    class Meta:
        verbose_name = "Гость"
        verbose_name_plural = "Гости"

    def __str__(self):
        return self.name

class HolidayEvent(models.Model):
    """Праздничное мероприятие"""
    name = models.CharField(max_length=200, verbose_name="Название мероприятия")
    event_date = models.DateField(verbose_name="Дата мероприятия")
    number_of_guests = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество гостей"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    # Связи
    guests = models.ManyToManyField(Guest, blank=True, verbose_name="Гости")
    selected_dishes = models.ManyToManyField(Dish, through='SelectedDish', verbose_name="Выбранные блюда")

    class Meta:
        verbose_name = "Праздничное мероприятие"
        verbose_name_plural = "Праздничные мероприятия"
        ordering = ['-event_date']

    def __str__(self):
        return f"{self.name} ({self.event_date})"

class SelectedDish(models.Model):
    """Связь мероприятия и выбранных блюд с количеством порций"""
    event = models.ForeignKey(HolidayEvent, on_delete=models.CASCADE)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    servings = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name="Количество порций"
    )

    class Meta:
        verbose_name = "Выбранное блюдо"
        verbose_name_plural = "Выбранные блюда"
        unique_together = ['event', 'dish']

    def __str__(self):
        return f"{self.event.name} - {self.dish.name}"

# В конце core/models.py добавьте:

class ShoppingList(models.Model):
    """Список покупок для мероприятия"""
    event = models.OneToOneField(
        HolidayEvent,
        on_delete=models.CASCADE,
        related_name='shopping_list'
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Список покупок для {self.event.name}"

class ShoppingItem(models.Model):
    """Элемент списка покупок"""
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity_needed = models.FloatField()
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    purchased = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.ingredient.name}: {self.quantity_needed}"