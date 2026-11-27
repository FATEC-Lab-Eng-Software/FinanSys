from collections.abc import Iterator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from src.core.database import get_db_session
from src.models.auth import User
from src.repositories.auth.user_repository import UserRepository
from src.shared.supabase.auth import SupabaseAuthAdapter


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


def test_pending_confirmation_registration_is_synced_for_admin_clients(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    user_id = uuid4()
    email = f"pending-{user_id.hex}@finansys.test"

    def register(self, submitted_email: str, password: str, name: str) -> dict[str, object]:
        assert submitted_email == email
        assert password == "SecurePassword123!"
        assert name == "Ana Cliente"
        return {"id": str(user_id), "email": email, "identities": [{"provider": "email"}]}

    monkeypatch.setattr(SupabaseAuthAdapter, "register", register)
    monkeypatch.setattr("src.services.auth.auth_controller.get_supabase_client", lambda: object())
    app.dependency_overrides[get_db_session] = lambda: session
    client = TestClient(app)
    try:
        response = client.post(
            "/auth/register",
            json={"name": "Ana Cliente", "email": email, "password": "SecurePassword123!"},
            headers={"Origin": "http://localhost:3000"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201, response.text
    users = UserRepository(session).list_clients(search=email, active=None, limit=10, offset=0)
    assert len(users) == 1
    assert users[0].id == user_id
    assert users[0].first_name == "Ana"
    assert users[0].last_name == "Cliente"
    assert users[0].last_access_at is None


def test_repeated_signup_placeholder_is_not_synced(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_user_id = uuid4()
    email = f"repeat-{fake_user_id.hex}@finansys.test"

    monkeypatch.setattr(
        SupabaseAuthAdapter,
        "register",
        lambda self, submitted_email, password, name: {
            "id": str(fake_user_id),
            "email": email,
            "identities": [],
        },
    )
    monkeypatch.setattr("src.services.auth.auth_controller.get_supabase_client", lambda: object())
    app.dependency_overrides[get_db_session] = lambda: session
    client = TestClient(app)
    try:
        response = client.post(
            "/auth/register",
            json={"name": "Cliente Repetido", "email": email, "password": "SecurePassword123!"},
            headers={"Origin": "http://localhost:3000"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201, response.text
    assert session.get(User, fake_user_id) is None
