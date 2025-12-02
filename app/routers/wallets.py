"""
Модуль API для управления кошельками пользователей.

Этот модуль предоставляет набор эндпоинтов для создания, удаления,
обновления баланса и получения информации о кошельках.
Используется FastAPI для обработки HTTP-запросов и SQLAlchemy для взаимодействия с базой данных.

Атрибуты:
    router (APIRouter): Маршрутизатор FastAPI для обработки запросов к кошелькам.

Функции:
    create_wallet: Создание нового кошелька.
    delete_wallet: Удаление кошелька по идентификатору.
    update_wallet_balance: Обновление баланса кошелька (пополнение или снятие средств).
    get_wallet_balance: Получение информации о кошельке по идентификатору.
"""

import uuid
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.wallet import Wallet
from app.schemas import WalletOperation, WalletResponse


from app.backend.db_depends import (
    get_session,
)  # Импортируем функцию, пред. сессию SQLAlchemy

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])
session = Annotated[
    AsyncSession, Depends(get_session)
]  # Аннотация типа для зависимости сессии


@router.post("/", response_model=WalletResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Создать новый кошелёк",
             response_description="Возвращает созданный кошелёк с автоматически сгенерированным UUID и нулевым балансом."
             )
async def create_wallet(session: session) -> WalletResponse:
    """
    Создаёт новый кошелёк с автоматически сгенерированным UUID и нулевым балансом.

    Возвращает:
        WalletResponse: Объект созданного кошелька с полями `id` и `balance`.

    Исключения:
        HTTPException: Возникает при ошибке создания кошелька.
                       Статус код: 500, детали: "Something went wrong: {ошибка}".
    """
    try:
        new_wallet = Wallet()  # UUID и balance=0.00 сгенерируются автоматически
        session.add(new_wallet)
        await session.commit()
        await session.refresh(new_wallet)
        return new_wallet
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Something went wrong: {e}")


@router.delete("/{wallet_id}",
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Удалить кошелёк",
               response_description="Кошелёк успешно удалён. Возвращает пустой ответ."
               )
async def delete_wallet(
    wallet_id: uuid.UUID,
    session: session,
) -> None:
    """
    Удаляет кошелёк по указанному идентификатору.

    Аргументы:
        wallet_id (UUID): Уникальный идентификатор кошелька.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Исключения:
        HTTPException: Возникает, если кошелёк не найден.
                       Статус код: 404, детали: "Wallet not found".
    """
    result = await session.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    await session.delete(wallet)
    await session.commit()
    return


@router.post("/{wallet_id}/operation", response_model=WalletResponse,
             summary="Обновить баланс кошелька",
             response_description="Возвращает обновлённый кошелёк с актуальным балансом."
             )
async def update_wallet_balance(
    wallet_id: uuid.UUID,
    operation: WalletOperation,
    session: session,
) -> WalletResponse:
    """
    Обновляет баланс кошелька в зависимости от типа операции (пополнение или снятие).

    Аргументы:
        wallet_id (UUID): Уникальный идентификатор кошелька.
        operation (WalletOperation): Объект с типом операции и суммой.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        WalletResponse: Объект кошелька с обновлённым балансом.

    Исключения:
        HTTPException: Возникает, если кошелёк не найден.
                       Статус код: 404, детали: "Wallet not found".
        HTTPException: Возникает при недостаточных средствах для снятия.
                       Статус код: 400, детали: "Insufficient funds".
    """
    result = await session.execute(
        select(Wallet).where(Wallet.id == wallet_id).with_for_update()
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    if operation.operation_type == "DEPOSIT":
        wallet.balance += Decimal(str(operation.amount))
    elif operation.operation_type == "WITHDRAW":
        if wallet.balance < operation.amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")
        wallet.balance -= Decimal(str(operation.amount))
    await session.commit()
    await session.refresh(wallet)
    return wallet


@router.get("/{wallet_id}",
            response_model=WalletResponse,
            summary="Получить информацию о кошельке",
            response_description="Возвращает информацию о кошельке по идентификатору."
            )
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    session: session,
) -> WalletResponse:
    """
    Возвращает информацию о кошельке по указанному идентификатору.

    Аргументы:
        wallet_id (UUID): Уникальный идентификатор кошелька.
        session (AsyncSession): Асинхронная сессия SQLAlchemy.

    Возвращает:
        WalletResponse: Объект кошелька с полями `id` и `balance`.

    Исключения:
        HTTPException: Возникает, если кошелёк не найден.
                       Статус код: 404, детали: "Wallet not found".
    """
    result = await session.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet
