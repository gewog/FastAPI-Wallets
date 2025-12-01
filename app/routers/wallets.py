import uuid
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.wallet import Wallet
from app.schemas import WalletOperation, WalletResponse


from app.backend.db_depends import get_session # Импортируем функцию, пред. сессию SQLAlchemy

router = APIRouter(prefix="/api/v1/wallets", tags=["wallets"])
session = Annotated[
    AsyncSession, Depends(get_session)
] # Аннотация типа для зависимости сессии


@router.post("/", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(session: session):
    """Функция создания кошелька."""
    try:
        new_wallet = Wallet()  # UUID и balance=0.00 сгенерируются автоматически
        session.add(new_wallet)
        await session.commit()
        await session.refresh(new_wallet)
        return new_wallet
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Something went wrong: {e}")

@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wallet(
    wallet_id: uuid.UUID,
    session: session,
):
    """Удаление кошелька по идентификатору."""
    result = await session.execute(
        select(Wallet).where(Wallet.id == wallet_id)
    )
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    await session.delete(wallet)
    await session.commit()
    return

@router.post("/{wallet_id}/operation", response_model=WalletResponse)
async def update_wallet_balance(
    wallet_id: uuid.UUID,
    operation: WalletOperation,
    session: session,
):
    # Используем SELECT ... FOR UPDATE для блокировки строки
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
            raise HTTPException(
                status_code=400, detail="Insufficient funds"
            )
        wallet.balance -= Decimal(str(operation.amount))
    await session.commit()
    await session.refresh(wallet)
    return wallet

@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet_balance(
    wallet_id: uuid.UUID,
    session: session,
):
    result = await session.execute(select(Wallet).where(Wallet.id == wallet_id))
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet