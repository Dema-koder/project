"""
holiday_menu URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Админка Django
    path('admin/', admin.site.urls),

    # Подключаем URL-ы из приложения core
    # Если у вас есть файл core/urls.py:
    path('', include('core.urls')),

    # Подключаем API (если создали приложение api)
    # path('api/', include('api.urls')),
]