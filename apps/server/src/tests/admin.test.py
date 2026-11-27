from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from src.core.auth_dependencies import require_authenticated_user
from src.core.database import get_db_session
from src.models.auth import User
from src.schemas.auth import AuthenticatedUser


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


def create_user(session: Session, *, role: str = "client", active: bool = True, **values: object) -> User:
    email = values.pop("email", f"{uuid4()}@finansys.test")
    user = User(
        id=uuid4(),
        email=email,
        role=role,
        is_active=active,
        **values,
    )
    session.add(user)
    session.commit()
    return user


@pytest.fixture
def admin_user(session: Session) -> User:
    return create_user(session, role="admin")


@pytest.fixture
def admin_client(session: Session, admin_user: User) -> Iterator[TestClient]:
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[require_authenticated_user] = lambda: AuthenticatedUser(
        id=str(admin_user.id), email=admin_user.email, role="admin"
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_admin_lists_clients_with_search_filter_and_pagination(
    admin_client: TestClient,
    session: Session,
) -> None:
    first = create_user(session, first_name="Ana", last_name="Silva", email="ana@finansys.test")
    create_user(session, first_name="Ana", last_name="Costa", email="ana.costa@finansys.test", active=False)
    create_user(session, first_name="Bruno", email="bruno@finansys.test")
    create_user(session, role="admin", email="outro-admin@finansys.test")

    response = admin_client.get("/admin/clients", params={"search": "ana", "active": "true", "page_size": 1})

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body["items"]] == [str(first.id)]
    assert body["page"] == 1
    assert body["page_size"] == 1
    assert body["has_more"] is False
    assert "transactions" not in body["items"][0]


def test_admin_overview_returns_client_account_metrics(
    admin_client: TestClient,
    session: Session,
) -> None:
    before = admin_client.get("/admin/overview").json()
    create_user(session)
    create_user(session, active=False)
    create_user(session, role="admin")

    response = admin_client.get("/admin/overview")

    assert response.status_code == 200
    assert response.json()["clients_total"] == before["clients_total"] + 2
    assert response.json()["clients_active"] == before["clients_active"] + 1
    assert response.json()["clients_suspended"] == before["clients_suspended"] + 1


def test_client_cannot_list_admin_clients(session: Session) -> None:
    client_user = create_user(session)
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[require_authenticated_user] = lambda: AuthenticatedUser(
        id=str(client_user.id), email=client_user.email, role="client"
    )
    client = TestClient(app)
    try:
        response = client.get("/admin/clients")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "admin_required"


def test_admin_can_suspend_and_reactivate_a_client(
    admin_client: TestClient,
    session: Session,
) -> None:
    client_user = create_user(session)

    suspended = admin_client.patch(f"/admin/clients/{client_user.id}/status", json={"is_active": False})

    assert suspended.status_code == 200
    assert suspended.json()["is_active"] is False
    session.refresh(client_user)
    assert client_user.is_active is False

    reactivated = admin_client.patch(f"/admin/clients/{client_user.id}/status", json={"is_active": True})

    assert reactivated.status_code == 200
    assert reactivated.json()["is_active"] is True


def test_admin_cannot_change_status_of_unknown_client(admin_client: TestClient) -> None:
    response = admin_client.patch(f"/admin/clients/{uuid4()}/status", json={"is_active": False})

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "client_not_found"
