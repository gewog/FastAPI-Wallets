"""
Основной модуль приложения FastAPI.

Этот модуль инициализирует FastAPI-приложение и подключает маршрутизаторы (роутеры)
для обработки HTTP-запросов. Является точкой входа для запуска сервера.

Атрибуты:
    app (FastAPI): Экземпляр FastAPI-приложения.

Функции:
    None: Все маршруты подключаются через метод `include_router`.
"""

from fastapi import FastAPI
from app.routers import wallets

# Инициализация FastAPI-приложения в режиме отладки.
app = FastAPI(debug=True)

# Подключение маршрутизатора для работы с кошельками.
app.include_router(wallets.router)
