import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from main import app
from src.core.database import get_db_session
from src.schemas.auth import AuthenticatedUser
from src.services.auth.errors import AuthFailure


USER = AuthenticatedUser(
    id="b381e1f0-8495-4b74-aadd-b5d3b662aafa",
    email="dev@example.com",
)
NOW = datetime(2026, 10, 1, 20, 0, tzinfo=timezone.utc)


class FakeDatabase:
    def __init__(self):
        self.last_activity_at = NOW - timedelta(minutes=14, seconds=59)
        self.fail = False
        self.activity_checks = []


class FakeUserAccessService:
    database = None

    def __init__(self, db):
        self.database = db

    def check_session_activity(self, user_id, now):
        if self.database.fail:
            raise AuthFailure(
                503,
                "user_store_unavailable",
                "Serviço de autenticação indisponível.",
                "user_store_unavailable",
            )
        self.database.activity_checks.append((user_id, now))
        if now - self.database.last_activity_at >= timedelta(minutes=15):
            return False
        self.database.last_activity_at = now
        return True

    def is_session_active(self, user_id, now):
        if self.database.fail:
            raise AuthFailure(
                503,
                "user_store_unavailable",
                "Serviço de autenticação indisponível.",
                "user_store_unavailable",
            )
        return now - self.database.last_activity_at < timedelta(minutes=15)


class FakeSessionService:
    current_user_error = None
    refresh_error = None
    refresh_calls = 0
    refreshed_user = USER

    def __init__(self, client):
        pass

    def current_user(self, access_token):
        if self.current_user_error:
            raise self.current_user_error
        return USER

    def refresh(self, refresh_token):
        type(self).refresh_calls += 1
        if self.refresh_error:
            raise self.refresh_error
        return type(self).refreshed_user, "new-access-token", "new-refresh-token", 3600

    def revoke(self, access_token):
        return None


@pytest.fixture
def auth_client(monkeypatch):
    database = FakeDatabase()
    app.dependency_overrides[get_db_session] = lambda: database
    monkeypatch.setattr(
        "src.services.auth.auth_controller.UserAccessService",
        FakeUserAccessService,
    )
    monkeypatch.setattr(
        "src.services.auth.auth_controller.SessionService",
        FakeSessionService,
    )
    monkeypatch.setattr(
        "src.services.auth.auth_controller.get_supabase_client",
        lambda: object(),
    )
    monkeypatch.setattr(
        "src.services.auth.auth_controller.utc_now",
        lambda: NOW,
        raising=False,
    )
    FakeSessionService.current_user_error = None
    FakeSessionService.refresh_error = None
    FakeSessionService.refresh_calls = 0
    FakeSessionService.refreshed_user = USER
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("finansys_access_token", "valid-access-token")
    client.cookies.set("finansys_refresh_token", "valid-refresh-token", path="/auth")
    yield client, database
    app.dependency_overrides.clear()


def _assert_cookies_cleared(response):
    headers = response.headers.get_list("set-cookie")
    assert any("finansys_access_token" in value and "max-age=0" in value.lower() for value in headers)
    assert any("finansys_refresh_token" in value and "max-age=0" in value.lower() for value in headers)


def _access_token_for(user_id):
    payload = base64.urlsafe_b64encode(json.dumps({"sub": user_id}).encode()).decode().rstrip("=")
    return f"header.{payload}.signature"


def test_active_session_before_fifteen_minutes_is_accepted_and_activity_is_renewed(auth_client):
    client, database = auth_client

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == USER.model_dump()
    assert database.last_activity_at == NOW
    assert database.activity_checks == [(USER.id, NOW)]


@pytest.mark.parametrize("inactive_for", [timedelta(minutes=15), timedelta(minutes=15, seconds=1)])
def test_session_at_or_after_fifteen_minutes_is_rejected_and_cookies_are_cleared(
    auth_client,
    inactive_for,
):
    client, database = auth_client
    database.last_activity_at = NOW - inactive_for

    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_session"
    _assert_cookies_cleared(response)
    assert database.last_activity_at == NOW - inactive_for


def test_expired_session_cannot_be_reactivated_by_refresh(auth_client):
    client, database = auth_client
    database.last_activity_at = NOW - timedelta(minutes=15)

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_session"
    _assert_cookies_cleared(response)
    assert FakeSessionService.refresh_calls == 0
    assert database.last_activity_at == NOW - timedelta(minutes=15)


def test_active_session_can_refresh_after_access_token_expiration(auth_client):
    client, database = auth_client
    client.cookies.set("finansys_access_token", _access_token_for(USER.id))
    FakeSessionService.current_user_error = AuthFailure(
        401,
        "invalid_session",
        "Sessão inválida ou expirada.",
        "invalid_session",
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 200
    assert FakeSessionService.refresh_calls == 1
    assert database.last_activity_at == NOW


def test_expired_access_token_does_not_rotate_refresh_for_idle_session(auth_client):
    client, database = auth_client
    database.last_activity_at = NOW - timedelta(minutes=15)
    client.cookies.set("finansys_access_token", _access_token_for(USER.id))
    FakeSessionService.current_user_error = AuthFailure(
        401,
        "invalid_session",
        "Sessão inválida ou expirada.",
        "invalid_session",
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert FakeSessionService.refresh_calls == 0
    _assert_cookies_cleared(response)


def test_expired_access_token_fails_closed_when_activity_store_is_unavailable(auth_client):
    client, database = auth_client
    database.fail = True
    client.cookies.set("finansys_access_token", _access_token_for(USER.id))
    FakeSessionService.current_user_error = AuthFailure(
        401,
        "invalid_session",
        "Sessão inválida ou expirada.",
        "invalid_session",
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "user_store_unavailable"
    assert FakeSessionService.refresh_calls == 0


def test_refresh_rejects_access_and_refresh_cookies_for_different_users(auth_client):
    client, _ = auth_client
    FakeSessionService.refreshed_user = AuthenticatedUser(
        id="2d6b119b-77d4-4e32-b6f3-b80c345319ec",
        email="other@example.com",
    )

    response = client.post("/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_session"
    _assert_cookies_cleared(response)


def test_activity_store_failure_fails_closed_with_service_unavailable(auth_client):
    client, database = auth_client
    database.fail = True

    response = client.get("/auth/me")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "user_store_unavailable"
    assert not response.headers.get_list("set-cookie")


@pytest.mark.parametrize(
    ("provider_error", "expected_status", "expected_code"),
    [
        (AuthFailure(401, "invalid_session", "Sessão inválida ou expirada.", "invalid_session"), 401, "invalid_session"),
        (AuthFailure(503, "authentication_unavailable", "Serviço de autenticação indisponível.", "provider_unavailable"), 503, "authentication_unavailable"),
    ],
)
def test_provider_invalid_or_unavailable_is_handled_without_exposing_details(
    auth_client,
    provider_error,
    expected_status,
    expected_code,
):
    client, _ = auth_client
    FakeSessionService.current_user_error = provider_error

    response = client.get("/auth/me")

    assert response.status_code == expected_status
    assert response.json()["detail"]["code"] == expected_code
    assert "provider" not in response.text
    if expected_status == 401:
        _assert_cookies_cleared(response)
    else:
        assert not response.headers.get_list("set-cookie")
