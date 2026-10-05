from collections.abc import Iterator
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from main import app
from src.core.database import get_db_session
from src.models.auth import User
from src.models.goal import Goal
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


def create_goal(session: Session, user: User, **overrides: object) -> Goal:
    values = {
        "name": "Meta de outro usuário",
        "category": "travel",
        "target_value": Decimal("1000.00"),
        "accumulated_value": Decimal("100.00"),
        "status": "pending",
    }
    values.update(overrides)
    goal = Goal(user_id=user.id, **values)
    session.add(goal)
    session.commit()
    return goal


def goal_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Reserva de emergência",
        "category": "other",
        "target_date": "2027-06-30",
        "target_value": "1000.00",
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


def test_create_goal_starts_pending_with_zero_accumulated(client: TestClient) -> None:
    response = client.post("/goals", json=goal_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Reserva de emergência"
    assert body["category"] == "other"
    assert body["target_date"] == "2027-06-30"
    assert body["target_value"] == "1000.00"
    assert body["accumulated_value"] == "0.00"
    assert body["status"] == "pending"
    assert "user_id" not in body


def test_create_goal_without_target_date(client: TestClient) -> None:
    response = client.post("/goals", json=goal_payload(target_date=None))

    assert response.status_code == 201
    assert response.json()["target_date"] is None


def test_create_goal_already_reached_is_done(client: TestClient) -> None:
    response = client.post("/goals", json=goal_payload(accumulated_value="1000.00"))

    assert response.status_code == 201
    assert response.json()["status"] == "done"


def test_create_goal_ignores_status_and_user_id_in_payload(
    client: TestClient,
    session: Session,
    owner: User,
    other_user: User,
) -> None:
    response = client.post(
        "/goals",
        json=goal_payload(status="done", user_id=str(other_user.id)),
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    saved = session.get(Goal, response.json()["id"])
    assert saved is not None
    assert saved.user_id == owner.id


@pytest.mark.parametrize(
    "overrides",
    [
        {"target_value": "0"},
        {"target_value": "-100.00"},
        {"target_value": "10.123"},
        {"accumulated_value": "-1.00"},
        {"category": "casino"},
        {"name": "   "},
        {"name": "x" * 101},
    ],
)
def test_create_goal_rejects_invalid_payload(client: TestClient, overrides: dict[str, object]) -> None:
    response = client.post("/goals", json=goal_payload(**overrides))

    assert response.status_code == 422


def test_list_returns_only_owner_goals(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    create_goal(session, other_user)
    created = client.post("/goals", json=goal_payload()).json()

    response = client.get("/goals")

    assert response.status_code == 200
    assert [goal["id"] for goal in response.json()] == [created["id"]]


def test_list_filters_by_status_and_category(client: TestClient) -> None:
    client.post("/goals", json=goal_payload(accumulated_value="1000.00"))
    client.post("/goals", json=goal_payload(category="travel"))
    expected = client.post("/goals", json=goal_payload()).json()

    response = client.get("/goals", params={"status": "pending", "category": "other"})

    assert response.status_code == 200
    assert [goal["id"] for goal in response.json()] == [expected["id"]]


def test_get_goal_of_another_user_returns_not_found(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    foreign = create_goal(session, other_user)

    response = client.get(f"/goals/{foreign.id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "goal_not_found"


def test_update_accumulated_value_reaching_target_marks_done(client: TestClient) -> None:
    created = client.post("/goals", json=goal_payload()).json()

    response = client.patch(f"/goals/{created['id']}", json={"accumulated_value": "1000.00"})

    assert response.status_code == 200
    assert response.json()["accumulated_value"] == "1000.00"
    assert response.json()["status"] == "done"


def test_update_raising_target_value_reopens_goal(client: TestClient) -> None:
    created = client.post("/goals", json=goal_payload(accumulated_value="1000.00")).json()

    response = client.patch(f"/goals/{created['id']}", json={"target_value": "2000.00"})

    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_update_changes_only_sent_fields(client: TestClient) -> None:
    created = client.post("/goals", json=goal_payload()).json()

    response = client.patch(f"/goals/{created['id']}", json={"name": "Viagem ao Chile"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Viagem ao Chile"
    assert body["target_value"] == created["target_value"]
    assert body["category"] == created["category"]


def test_update_allows_clearing_target_date(client: TestClient) -> None:
    created = client.post("/goals", json=goal_payload()).json()

    response = client.patch(f"/goals/{created['id']}", json={"target_date": None})

    assert response.status_code == 200
    assert response.json()["target_date"] is None


@pytest.mark.parametrize(
    "payload",
    [{}, {"name": None}, {"target_value": None}, {"accumulated_value": "-5.00"}, {"status": "done"}],
)
def test_update_rejects_invalid_payload(client: TestClient, payload: dict[str, object]) -> None:
    created = client.post("/goals", json=goal_payload()).json()

    response = client.patch(f"/goals/{created['id']}", json=payload)

    assert response.status_code == 422


def test_update_goal_of_another_user_returns_not_found(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    foreign = create_goal(session, other_user)

    response = client.patch(f"/goals/{foreign.id}", json={"accumulated_value": "999.00"})

    assert response.status_code == 404
    session.refresh(foreign)
    assert foreign.accumulated_value == Decimal("100.00")


def test_delete_goal_removes_it(client: TestClient) -> None:
    created = client.post("/goals", json=goal_payload()).json()

    response = client.delete(f"/goals/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/goals/{created['id']}").status_code == 404


def test_delete_goal_of_another_user_returns_not_found(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    foreign = create_goal(session, other_user)

    response = client.delete(f"/goals/{foreign.id}")

    assert response.status_code == 404
    assert session.scalar(select(Goal).where(Goal.id == foreign.id)) is not None


@pytest.mark.parametrize(
    ("target_value", "accumulated_value", "remaining_value", "remaining_percentage"),
    [
        ("1000.00", "0", "1000.00", "100.00"),
        ("1000.00", "250.00", "750.00", "75.00"),
        ("300.00", "100.00", "200.00", "66.67"),
        ("1000.00", "1000.00", "0.00", "0.00"),
        ("1000.00", "1500.00", "0.00", "0.00"),
    ],
)
def test_progress_returns_remaining_value_and_percentage(
    client: TestClient,
    target_value: str,
    accumulated_value: str,
    remaining_value: str,
    remaining_percentage: str,
) -> None:
    created = client.post(
        "/goals",
        json=goal_payload(target_value=target_value, accumulated_value=accumulated_value),
    ).json()

    response = client.get(f"/goals/{created['id']}/progress")

    assert response.status_code == 200
    assert response.json() == {
        "goal_id": created["id"],
        "remaining_value": remaining_value,
        "remaining_percentage": remaining_percentage,
    }


def test_progress_of_another_user_goal_returns_not_found(
    client: TestClient,
    session: Session,
    other_user: User,
) -> None:
    foreign = create_goal(session, other_user)

    response = client.get(f"/goals/{foreign.id}/progress")

    assert response.status_code == 404


def test_requests_without_session_are_rejected(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/goals")

    assert response.status_code == 401