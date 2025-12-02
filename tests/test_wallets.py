"""
Модуль тестов для API кошельков.

Этот модуль содержит набор тестов для проверки функциональности API кошельков,
включая создание, получение баланса, пополнение, снятие средств и удаление кошельков.
Используется pytest для написания тестов, TestClient для имитации HTTP-запросов,
и SQLite в памяти для изоляции тестов от основной базы данных.

Функции:
    test_db: Фикстура для создания тестовой базы данных в памяти.
    client: Фикстура для создания тестового клиента FastAPI с переопределённой зависимостью сессии.
    test_create_wallet: Тест создания нового кошелька.
    test_get_wallet_balance: Тест получения баланса кошелька.
    test_deposit_to_wallet: Тест пополнения кошелька.
    test_withdraw_from_wallet: Тест снятия средств с кошелька.
    test_withdraw_insufficient_funds: Тест попытки снять больше средств, чем на балансе.
    test_delete_wallet: Тест удаления кошелька.
    test_get_nonexistent_wallet: Тест получения несуществующего кошелька.
"""


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
    """
    Фикстура для создания тестовой базы данных в памяти.

    Создаёт асинхронный движок SQLAlchemy с подключением к SQLite в памяти,
    создаёт все таблицы перед выполнением тестов и удаляет их после завершения.
    Используется для изоляции тестов от основной базы данных.

    Yields:
        AsyncEngine: Асинхронный движок SQLAlchemy для тестовой базы данных.
    """
    # Создаём тестовый движок и подключаемся к базе данных в памяти
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    # Создаём таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    # Удаляем таблицы после завершения тестов
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Переопределяем зависимость get_session для тестов
@pytest.fixture
async def client(test_db):
    """
    Фикстура для создания тестового клиента FastAPI.

    Создаёт тестового клиента FastAPI с переопределённой зависимостью `get_session`,
    которая использует тестовую базу данных. Это позволяет тестировать API
    без подключения к реальной базе данных.

    Аргументы:
        test_db (AsyncEngine): Тестовый движок базы данных.

    Yields:
        TestClient: Тестовый клиент FastAPI для выполнения HTTP-запросов.
    """
    # Создаём фабрику сессий для тестовой базы данных
    async_session = async_sessionmaker(bind=test_db, expire_on_commit=False)

    # Переопределяем зависимость get_session для тестов
    async def override_get_session():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)

    # Удаляем переопределение зависимости после завершения тестов
    del app.dependency_overrides[get_session]


# Тест: создание кошелька
@pytest.mark.asyncio
async def test_create_wallet(client):
    """
    Тест создания нового кошелька.

    Проверяет, что кошелёк успешно создаётся и возвращает корректные данные:
    уникальный идентификатор и нулевой баланс.

    Аргументы:
        client (TestClient): Тестовый клиент FastAPI.
    """
    response = client.post("/api/v1/wallets/")
    assert response.status_code == 201
    wallet = response.json()
    assert "id" in wallet
    assert wallet["balance"] == 0.0


# Тест: получение баланса кошелька
@pytest.mark.asyncio
async def test_get_wallet_balance(client):
    """
    Тест получения баланса кошелька.

    Сначала создаёт кошелёк, затем проверяет, что баланс возвращается корректно.

    Аргументы:
        client (TestClient): Тестовый клиент FastAPI.
    """
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
    """
    Тест пополнения кошелька.

    Сначала создаёт кошелёк, затем пополняет его на указанную сумму
    и проверяет, что баланс обновляется корректно.

    Аргументы:
        client (TestClient): Тестовый клиент FastAPI.
    """
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
    """
    Тест снятия средств с кошелька.

    Сначала создаёт кошелёк, пополняет его, затем снимает часть средств
    и проверяет, что баланс обновляется корректно.

    Аргументы:
        client (TestClient): Тестовый клиент FastAPI.
    """
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
    """
    Тест попытки снять больше средств, чем на балансе.

    Проверяет, что при попытке снять сумму, превышающую баланс,
    возвращается ошибка с кодом 400 и сообщением "Insufficient funds".

    Аргументы:
        client (TestClient): Тестовый клиент FastAPI.
    """
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
    """
    Тест удаления кошелька.

    Сначала создаёт кошелёк, затем удаляет его и проверяет,
    что кошелёк действительно удалён (возвращается ошибка 404).

    Аргументы:
        client (TestClient): Тестовый клиент FastAPI.
    """
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
    """
    Тест получения несуществующего кошелька.

    Проверяет, что при попытке получить информацию о несуществующем кошельке
    возвращается ошибка с кодом 404 и сообщением "Wallet not found".

    Аргументы:
        client (TestClient): Тестовый клиент FastAPI.
    """
    nonexistent_id = uuid.uuid4()
    response = client.get(f"/api/v1/wallets/{nonexistent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Wallet not found"
