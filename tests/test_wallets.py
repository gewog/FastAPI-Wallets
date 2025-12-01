import pytest
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.backend.db_depends import get_session
from app.models.wallet import Base, Wallet

# Создаём тестовый движок и фабрику сессий
@pytest.fixture(scope="function")
async def test_db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# Переопределяем зависимость get_session для тестов
@pytest.fixture
async def client(test_db):
    async_session = async_sessionmaker(bind=test_db, expire_on_commit=False)

    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    del app.dependency_overrides[get_session]

# Тест: создание кошелька
@pytest.mark.asyncio
async def test_create_wallet(client):
    response = client.post("/api/v1/wallets/")
    assert response.status_code == 201
    wallet = response.json()
    assert "id" in wallet
    assert wallet["balance"] == 0.0

# Тест: получение баланса кошелька
@pytest.mark.asyncio
async def test_get_wallet_balance(client):
    # Создаём кошелёк
    create_response = client.post("/api/v1/wallets/")
    wallet_id = create_response.json()["id"]

    # Проверяем баланс
    response = client.get(f"/api/v1/wallets/{wallet_id}")
    assert response.status_code == 200
    assert response.json()["balance"] == 0.0

# Тест: пополнение кошелька
@pytest.mark.asyncio
async def test_deposit_to_wallet(client):
    # Создаём кошелёк
    create_response = client.post("/api/v1/wallets/")
    wallet_id = create_response.json()["id"]

    # Пополняем
    deposit_response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 100.50},
    )
    assert deposit_response.status_code == 200
    assert deposit_response.json()["balance"] == 100.50

# Тест: снятие средств с кошелька
@pytest.mark.asyncio
async def test_withdraw_from_wallet(client):
    # Создаём кошелёк
    create_response = client.post("/api/v1/wallets/")
    wallet_id = create_response.json()["id"]

    # Пополняем
    client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 200.00},
    )

    # Снимаем
    withdraw_response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 50.50},
    )
    assert withdraw_response.status_code == 200
    assert withdraw_response.json()["balance"] == 149.50

# Тест: попытка снять больше, чем на балансе
@pytest.mark.asyncio
async def test_withdraw_insufficient_funds(client):
    # Создаём кошелёк
    create_response = client.post("/api/v1/wallets/")
    wallet_id = create_response.json()["id"]

    # Пополняем
    client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 10.00},
    )

    # Пытаемся снять больше, чем на балансе
    withdraw_response = client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "WITHDRAW", "amount": 20.00},
    )
    assert withdraw_response.status_code == 400
    assert withdraw_response.json()["detail"] == "Insufficient funds"

# Тест: удаление кошелька
@pytest.mark.asyncio
async def test_delete_wallet(client):
    # Создаём кошелёк
    create_response = client.post("/api/v1/wallets/")
    wallet_id = create_response.json()["id"]

    # Удаляем
    delete_response = client.delete(f"/api/v1/wallets/{wallet_id}")
    assert delete_response.status_code == 204

    # Проверяем, что кошелёк удалён
    get_response = client.get(f"/api/v1/wallets/{wallet_id}")
    assert get_response.status_code == 404

# Тест: попытка получить несуществующий кошелёк
@pytest.mark.asyncio
async def test_get_nonexistent_wallet(client):
    nonexistent_id = uuid.uuid4()
    response = client.get(f"/api/v1/wallets/{nonexistent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"
