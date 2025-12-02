"""
Модуль для управления асинхронными сессиями SQLAlchemy в FastAPI.

Этот модуль предоставляет функцию-зависимость для FastAPI, которая создаёт
и управляет асинхронными сессиями SQLAlchemy. Сессии автоматически закрываются
после завершения обработки запроса, что гарантирует корректное освобождение ресурсов.

Функции:
    get_session(): Асинхронная функция-зависимость для FastAPI, предоставляющая сессию SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db import session


async def get_session() -> AsyncSession:
    """
    Асинхронная функция-зависимость для FastAPI, предоставляющая сессию SQLAlchemy.

    Создаёт новую асинхронную сессию SQLAlchemy и управляет её жизненным циклом.
    Сессия автоматически закрывается после завершения запроса, даже если произошла ошибка.

    Использование:
        ```python
        from fastapi import Depends, APIRouter

        router = APIRouter()

        @router.get("/items/")
        async def read_items(db: AsyncSession = Depends(get_session)):
            # Использование сессии `db` для работы с базой данных
            pass
        ```

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy для выполнения запросов к базе данных.

    Примечание:
        Сессия гарантированно закрывается после завершения работы,
        даже если в процессе выполнения возникнет исключение.
    """
    async with session() as ss:
        try:
            yield ss
        finally:
            await ss.close()  # Закрывает сессию при ошибке
