from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from main import app
from src.core.database import get_db_session
from src.schemas.auth import AuthenticatedUser
from src.services.auth.errors import AuthFailure


class FakeLockoutState:
    def __init__(self):
        self.now = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
        self.attempts = 0
        self.locked_until = None
        self.login_calls = 0
        self.result = "invalid"
        self.fail_check = False
        self.fail_record = False


class FakeUserAccessService:
    state = None

    def __init__(self, db):
        self.state = db

    def check_login_lockout(self, email):
        if self.state.fail_check:
            raise AuthFailure(503, "user_store_unavailable", "NÃ£o foi possÃ­vel concluir a autenticaÃ§Ã£o.", "user_store_unavailable")
        if self.state.locked_until and self.state.now < self.state.locked_until:
            return self.state.locked_until
        if self.state.locked_until and self.state.now >= self.state.locked_until:
            self.state.locked_until = None
            self.state.attempts = 0
        return None

    def record_failed_login(self, email):
        if self.state.fail_record:
            raise AuthFailure(503, "user_store_unavailable", "NÃ£o foi possÃ­vel concluir a autenticaÃ§Ã£o.", "user_store_unavailable")
        self.state.attempts += 1
        if self.state.attempts >= 5:
            self.state.locked_until = self.state.now + timedelta(minutes=10)
            return self.state.locked_until
        return None

    def record_successful_login(self, user):
        self.state.attempts = 0
        self.state.locked_until = None


class FakeLoginService:
    state = None

    def __init__(self, client):
        self.state = client

    def authenticate(self, credentials):
        self.state.login_calls += 1
        if self.state.result == "invalid":
            raise AuthFailure(401, "invalid_credentials", "E-mail ou senha invÃ¡lidos.", "invalid_credentials")
        if self.state.result == "provider_unavailable":
            raise AuthFailure(503, "authentication_unavailable", "ServiÃ§o de autenticaÃ§Ã£o indisponÃ­vel.", "provider_unavailable")
        return AuthenticatedUser(id="b381e1f0-8495-4b74-aadd-b5d3b662aafa", email=credentials.email), "access", "refresh", 3600


def _client(monkeypatch, state):
    app.dependency_overrides[get_db_session] = lambda: state
    monkeypatch.setattr("src.services.auth.auth_controller.UserAccessService", FakeUserAccessService)
    monkeypatch.setattr("src.services.auth.auth_controller.LoginService", FakeLoginService)
    monkeypatch.setattr("src.services.auth.auth_controller.get_supabase_client", lambda: state)
    monkeypatch.setattr("src.services.auth.auth_controller.utc_now", lambda: state.now, raising=False)
    return TestClient(app)


def _login(client, password="wrongpass"):
    return client.post("/auth/login", json={"email": "dev@example.com", "password": password})


def test_fifth_invalid_password_locks_account_for_ten_minutes(monkeypatch):
    state = FakeLockoutState()
    client = _client(monkeypatch, state)
    try:
        responses = [_login(client) for _ in range(5)]
    finally:
        app.dependency_overrides.clear()

    assert [response.status_code for response in responses] == [401, 401, 401, 401, 423]
    body = responses[-1].json()["detail"]
    assert body["code"] == "account_temporarily_locked"
    locked_until = datetime.fromisoformat(body["locked_until"].replace("Z", "+00:00"))
    assert locked_until == datetime(2026, 10, 1, 12, 10, tzinfo=timezone.utc)
    assert responses[-1].headers["retry-after"] == "600"
    assert state.attempts == 5


def test_locked_account_does_not_call_supabase(monkeypatch):
    state = FakeLockoutState()
    state.attempts = 5
    state.locked_until = state.now + timedelta(minutes=10)
    client = _client(monkeypatch, state)
    try:
        response = _login(client)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 423
    assert response.json()["detail"]["code"] == "account_temporarily_locked"
    assert state.login_calls == 0


def test_login_is_allowed_at_exact_lock_expiration(monkeypatch):
    state = FakeLockoutState()
    state.attempts = 5
    state.locked_until = state.now + timedelta(minutes=10)
    state.now = state.locked_until
    client = _client(monkeypatch, state)
    try:
        response = _login(client)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert state.login_calls == 1
    assert state.attempts == 1
    assert state.locked_until is None


def test_successful_login_resets_attempts_and_lockout(monkeypatch):
    state = FakeLockoutState()
    state.attempts = 4
    state.result = "success"
    client = _client(monkeypatch, state)
    try:
        response = _login(client, password="correctpass")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert state.attempts == 0
    assert state.locked_until is None


def test_provider_and_network_failures_do_not_increment_attempts(monkeypatch):
    state = FakeLockoutState()
    state.result = "provider_unavailable"
    client = _client(monkeypatch, state)
    try:
        response = _login(client)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert state.attempts == 0


def test_database_check_failure_fails_closed_without_provider_call(monkeypatch):
    state = FakeLockoutState()
    state.fail_check = True
    client = _client(monkeypatch, state)
    try:
        response = _login(client)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert state.login_calls == 0
    assert state.attempts == 0


def test_database_record_failure_does_not_count_invalid_password(monkeypatch):
    state = FakeLockoutState()
    state.fail_record = True
    client = _client(monkeypatch, state)
    try:
        response = _login(client)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert state.attempts == 0
