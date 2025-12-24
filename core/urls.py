from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create/', views.create_event, name='create_event'),
    path('event/<int:event_id>/guests/', views.add_guests, name='add_guests'),
    path('event/<int:event_id>/menu/', views.generate_menu, name='generate_menu'),
    path('event/<int:event_id>/shopping/', views.generate_shopping_list, name='shopping_list'),
    path('event/<int:event_id>/shopping/debug/', views.generate_shopping_list_debug, name='shopping_debug'),
    path('event/<int:event_id>/show/', views.show_event, name='show_event'),
    path('event/<int:event_id>/guest/<int:guest_id>/edit/', views.edit_guest, name='edit_guest'),
    path('event/<int:event_id>/guest/<int:guest_id>/delete/', views.delete_guest, name='delete_guest'),
    path('dishes/', views.dish_list, name='dish_list'),
]
