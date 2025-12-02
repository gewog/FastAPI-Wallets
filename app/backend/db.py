"""
Модуль для тестирования подключения к базе данных PostgreSQL с использованием SQLAlchemy и asyncio.

Этот модуль предоставляет асинхронную функцию для проверки подключения к базе данных
и получения её версии. Используется для диагностики и тестирования на этапе разработки.

Атрибуты:
    engine (AsyncEngine): Асинхронный движок SQLAlchemy для подключения к базе данных.
    session (async_sessionmaker): Фабрика для создания асинхронных сессий SQLAlchemy.

Функции:
    get_version(): Асинхронная функция для выполнения тестового запроса к базе данных.
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.backend.settings import setting


engine = create_async_engine(setting.get_path, echo=True)
session = async_sessionmaker(bind=engine)


async def get_version() -> None:
    """
    Тестовая функция для получения версии PostgreSQL.

    Выполняет запрос `SELECT version();` и выводит результат в консоль.
    Эта функция предназначена для проверки подключения к базе данных
    и должна быть удалена после завершения тестирования.
    """
    try:
        async with session() as ss:
            res = await ss.execute(text("select version();"))
            print(res.all())
    except Exception as e:
        print(e)
    finally:
        await ss.close()


if __name__ == "__main__":
    asyncio.run(get_version())
