"""
Модуль для работы с базой данных.

Этот модуль предоставляет функции для инициализации таблиц,
тестирования подключения к PostgreSQL и получения данных из базы.
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
