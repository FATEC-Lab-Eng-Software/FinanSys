from collections.abc import Iterator
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from main import app
from src.core.database import get_db_session
from src.models.auth import User
from src.models.transaction import Transaction
from src.schemas.auth import AuthenticatedUser
from src.routers.transactions import get_current_user


@pytest.fixture
def session() -> Iterator[Session]:
    source = get_db_session()
    base_session = next(source)
    connection = base_session.get_bind().connect()
    outer_transaction = connection.begin()
    test_session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield test_session
    finally:
        test_session.close()
        outer_transaction.rollback()
        connection.close()
        source.close()


def create_user(session: Session) -> User:
    user = User(id=uuid4(), email=f"{uuid4()}@finansys.test")
    session.add(user)
    session.commit()
    return user


def create_transaction(session: Session, user: User, **overrides: object) -> Transaction:
    values = {
        "type": "inflow",
        "category": "work",
        "transaction_date": date(2026, 9, 1),
        "value": Decimal("10.00"),
        "source_money": "Conta corrente",
    }
    values.update(overrides)
    transaction = Transaction(user_id=user.id, **values)
    session.add(transaction)
    session.commit()
    return transaction


def transaction_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": "outflow",
        "category": "food",
        "transaction_date": "2026-10-01",
        "value": "150.00",
        "source_money": "Cartão de crédito",
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def owner(session: Session) -> User:
    return create_user(session)


@pytest.fixture
def other_user(session: Session) -> User:
    return create_user(session)


@pytest.fixture
def client(session: Session, owner: User) -> Iterator[TestClient]:
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=str(owner.id),
        email=owner.email,
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def anonymous_client(session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_transaction_returns_created_transaction(client: TestClient) -> None:
    response = client.post("/transactions", json=transaction_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["type"] == "outflow"
    assert body["category"] == "food"
    assert body["transaction_date"] == "2026-10-01"
    assert body["value"] == "150.00"
    assert body["source_money"] == "Cartão de crédito"
    assert "user_id" not in body


def test_create_transaction_ignores_user_id_in_payload(
    client: TestClient,
    session: Session,
    owner: User,
    other_user: User,
) -> None:
    response = client.post("/transactions", json=transaction_payload(user_id=str(other_user.id)))

    assert response.status_code == 201
    saved = session.get(Transaction, response.json()["id"])
    assert saved is not None
    assert saved.user_id == owner.id


@pytest.mark.parametrize("value", ["0", "-10.00", "10.123"])
def test_create_transaction_rejects_invalid_value(client: TestClient, value: str) -> None:
    response = client.post("/transactions", json=transaction_payload(value=value))

    assert response.status_code == 422


def test_create_transaction_rejects_unknown_category(client: TestClient) -> None:
    response = client.post("/transactions", json=transaction_payload(category="casino"))

    assert response.status_code == 422


def test_create_transaction_rejects_blank_source_money(client: TestClient) -> None:
    response = client.post("/transactions", json=transaction_payload(source_money="   "))

    assert response.status_code == 422


def test_list_returns_only_owner_transactions(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    create_transaction(session, other_user)
    created = client.post("/transactions", json=transaction_payload()).json()

    response = client.get("/transactions")

    assert response.status_code == 200
    assert [transaction["id"] for transaction in response.json()] == [created["id"]]


def test_list_orders_by_most_recent_date(client: TestClient) -> None:
    older = client.post("/transactions", json=transaction_payload(transaction_date="2026-09-01")).json()
    newer = client.post("/transactions", json=transaction_payload(transaction_date="2026-10-01")).json()

    response = client.get("/transactions")

    assert [transaction["id"] for transaction in response.json()] == [newer["id"], older["id"]]


def test_list_filters_by_period_type_and_category(client: TestClient) -> None:
    client.post("/transactions", json=transaction_payload(transaction_date="2026-08-15"))
    client.post("/transactions", json=transaction_payload(type="inflow", category="work"))
    expected = client.post("/transactions", json=transaction_payload(transaction_date="2026-09-20")).json()

    response = client.get(
        "/transactions",
        params={
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "type": "outflow",
            "category": "food",
        },
    )

    assert response.status_code == 200
    assert [transaction["id"] for transaction in response.json()] == [expected["id"]]


def test_list_rejects_inverted_period(client: TestClient) -> None:
    response = client.get(
        "/transactions",
        params={"start_date": "2026-10-01", "end_date": "2026-09-01"},
    )

    assert response.status_code == 422


def test_get_transaction_returns_owner_transaction(client: TestClient) -> None:
    created = client.post("/transactions", json=transaction_payload()).json()

    response = client.get(f"/transactions/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_transaction_of_another_user_returns_not_found(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    foreign = create_transaction(session, other_user)

    response = client.get(f"/transactions/{foreign.id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "transaction_not_found"


def test_update_transaction_changes_only_sent_fields(client: TestClient) -> None:
    created = client.post("/transactions", json=transaction_payload()).json()

    response = client.patch(f"/transactions/{created['id']}", json={"value": "199.90"})

    assert response.status_code == 200
    body = response.json()
    assert body["value"] == "199.90"
    assert body["category"] == created["category"]
    assert body["source_money"] == created["source_money"]


@pytest.mark.parametrize("payload", [{}, {"category": None}, {"value": "-1.00"}])
def test_update_transaction_rejects_invalid_payload(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    created = client.post("/transactions", json=transaction_payload()).json()

    response = client.patch(f"/transactions/{created['id']}", json=payload)

    assert response.status_code == 422


def test_update_transaction_of_another_user_returns_not_found(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    foreign = create_transaction(session, other_user)

    response = client.patch(f"/transactions/{foreign.id}", json={"value": "1.00"})

    assert response.status_code == 404
    session.refresh(foreign)
    assert foreign.value == Decimal("10.00")


def test_delete_transaction_removes_it(client: TestClient) -> None:
    created = client.post("/transactions", json=transaction_payload()).json()

    response = client.delete(f"/transactions/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/transactions/{created['id']}").status_code == 404


def test_delete_transaction_of_another_user_returns_not_found(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    foreign = create_transaction(session, other_user)

    response = client.delete(f"/transactions/{foreign.id}")

    assert response.status_code == 404
    assert session.scalar(select(Transaction).where(Transaction.id == foreign.id)) is not None


def test_requests_without_session_are_rejected(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/transactions")

    assert response.status_code == 401