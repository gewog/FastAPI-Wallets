"""
Модуль для определения SQLAlchemy-моделей базы данных.

Этот модуль содержит базовый класс `Base` для всех SQLAlchemy-моделей,
а также модель `Wallet`, представляющую кошелёк пользователя.
Модели используются для взаимодействия с базой данных PostgreSQL
с поддержкой UUID и числовых типов данных.

Классы:
    Base: Базовый класс для всех SQLAlchemy-моделей.
    Wallet: Модель кошелька с полями `id` и `balance`.
"""

import uuid
from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.

    Наследуясь от этого класса, другие классы становятся SQLAlchemy-моделями,
    которые могут быть сопоставлены с таблицами в базе данных.
    Используется для объявления таблиц и их полей.

    Атрибуты:
        None: Этот класс не содержит собственных атрибутов,
              но предоставляет базовую функциональность для моделей.
    """

    pass


class Wallet(Base):
    """
    Модель кошелька, представляющая учётную запись пользователя с балансом.

    Атрибуты:
        id (UUID): Уникальный идентификатор кошелька.
                   Используется UUID для глобальной уникальности.
                   Значение по умолчанию генерируется автоматически.
        balance (float): Текущий баланс кошелька.
                         Хранится как числовое значение с точностью до 2 знаков после запятой.
                         Значение по умолчанию: 0.00.
    """

    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
