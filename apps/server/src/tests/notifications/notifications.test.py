from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from src.core.database import get_db_session
from src.models.auth import User
from src.models.notification import Notification
from src.routers.transactions import get_current_user
from src.schemas.auth import AuthenticatedUser


def notification_session() -> Iterator[Session]:
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


def create_notification(session: Session, user: User, title: str) -> Notification:
    notification = Notification(
        user_id=user.id,
        category="transaction",
        title=title,
        description="Notificação de teste",
    )
    session.add(notification)
    session.commit()
    return notification


@pytest.fixture
def session() -> Iterator[Session]:
    yield from notification_session()


@pytest.fixture
def owner(session: Session) -> User:
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


def test_creating_transaction_stages_notification_with_transaction(client: TestClient) -> None:
    response = client.post(
        "/transactions",
        json={
            "type": "inflow",
            "category": "work",
            "transaction_date": "2026-11-21",
            "value": "3200.00",
            "source_money": "Salário",
        },
    )

    assert response.status_code == 201
    notifications = client.get("/notifications").json()
    assert len(notifications) == 1
    assert notifications[0]["category"] == "transaction"
    assert notifications[0]["title"] == "Entrada registrada"
    assert notifications[0]["description"] == "Salário: R$ 3200.00."


def test_completing_goal_creates_single_notification(client: TestClient) -> None:
    created = client.post(
        "/goals",
        json={"name": "Reserva", "category": "other", "target_value": "1000.00"},
    ).json()

    completed = client.patch(f"/goals/{created['id']}", json={"accumulated_value": "1000.00"})
    repeated_update = client.patch(f"/goals/{created['id']}", json={"name": "Reserva atualizada"})

    assert completed.status_code == 200
    assert repeated_update.status_code == 200
    notifications = client.get("/notifications").json()
    assert len(notifications) == 1
    assert notifications[0]["category"] == "goal"
    assert notifications[0]["title"] == "Meta concluída"
    assert "Reserva" in notifications[0]["description"]


def test_creating_already_completed_goal_creates_notification(client: TestClient) -> None:
    response = client.post(
        "/goals",
        json={
            "name": "Viagem",
            "category": "travel",
            "target_value": "500.00",
            "accumulated_value": "500.00",
        },
    )

    assert response.status_code == 201
    notifications = client.get("/notifications").json()
    assert len(notifications) == 1
    assert notifications[0]["category"] == "goal"


def test_notification_endpoints_only_change_current_users_items(
    client: TestClient,
    session: Session,
    owner: User,
) -> None:
    first = create_notification(session, owner, "Primeira")
    second = create_notification(session, owner, "Segunda")
    second_id = second.id
    other_user = create_user(session)
    foreign = create_notification(session, other_user, "Privada")
    foreign_id = foreign.id

    deleted = client.delete(f"/notifications/{first.id}")
    cleared = client.delete("/notifications")

    assert deleted.status_code == 204
    assert cleared.status_code == 204
    assert client.get("/notifications").json() == []
    assert session.get(Notification, foreign_id) is not None
    assert session.get(Notification, second_id) is None


def test_deleting_another_users_notification_returns_not_found(
    client: TestClient,
    session: Session,
) -> None:
    other_user = create_user(session)
    foreign = create_notification(session, other_user, "Privada")

    response = client.delete(f"/notifications/{foreign.id}")

    assert response.status_code == 404
    assert session.get(Notification, foreign.id) is not None


def test_notifications_require_authenticated_user(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/notifications")

    assert response.status_code == 401
