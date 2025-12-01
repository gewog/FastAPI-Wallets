import uuid
from sqlalchemy import Numeric
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import (Mapped, mapped_column, DeclarativeBase)

class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.

    Наследуясь от этого класса, другие классы становятся SQLAlchemy-моделями,
    которые могут быть преобразованы в таблицы базы данных.
    """
    pass

class Wallet(Base):
    """Модель кошелька"""
    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        index=True,
        default=uuid.uuid4
    )
    balance: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0.00
    )