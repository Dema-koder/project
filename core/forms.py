from django import forms
from django.core.validators import MinValueValidator
from .models import HolidayEvent, Guest, Dish

class HolidayEventForm(forms.ModelForm):
    """Форма для создания праздничного мероприятия"""
    number_of_guests = forms.IntegerField(
        min_value=1,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Количество гостей"
    )

    event_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Дата мероприятия"
    )

    class Meta:
        model = HolidayEvent
        fields = ['name', 'event_date', 'number_of_guests']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class GuestPreferenceForm(forms.Form):
    """Форма для ввода предпочтений гостей"""
    def __init__(self, *args, **kwargs):
        guests_count = kwargs.pop('guests_count', 1)
        super().__init__(*args, **kwargs)

        # Динамически создаем поля для каждого гостя
        for i in range(guests_count):
            self.fields[f'guest_{i}_name'] = forms.CharField(
                max_length=100,
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': f'Имя гостя {i+1}'
                }),
                label=f"Гость {i+1}"
            )

            self.fields[f'guest_{i}_dishes'] = forms.ModelMultipleChoiceField(
                queryset=Dish.objects.all(),
                widget=forms.SelectMultiple(attrs={
                    'class': 'form-control select2-multiple',
                    'style': 'height: 150px;'
                }),
                required=False,
                label=f"Любимые блюда гостя {i+1}"
            )

class MenuSelectionForm(forms.Form):
    """Форма для выбора блюд в меню"""
    def __init__(self, *args, **kwargs):
        suggested_dishes = kwargs.pop('suggested_dishes', [])
        super().__init__(*args, **kwargs)

        for i, dish_data in enumerate(suggested_dishes):
            dish = dish_data['dish']
            self.fields[f'dish_{dish.id}'] = forms.BooleanField(
                initial=True,
                required=False,
                label=f"{dish.name} ({dish.dish_type})",
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-check-input'
                })
            )

            self.fields[f'servings_{dish.id}'] = forms.IntegerField(
                min_value=1,
                initial=dish_data.get('servings', 1),
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'style': 'width: 80px;'
                }),
                label="Порций"
            )

class DishFilterForm(forms.Form):
    """Форма фильтрации блюд"""
    dish_type = forms.ChoiceField(
        # Временно убираем запрос к БД
        choices=[('', 'Все типы')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    difficulty = forms.ChoiceField(
        choices=[('', 'Любая сложность'), ('easy', 'Легко'), ('medium', 'Средне'), ('hard', 'Сложно')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    max_cooking_time = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Макс. время (мин)'
        })
    )

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск блюд...'
        })
    )