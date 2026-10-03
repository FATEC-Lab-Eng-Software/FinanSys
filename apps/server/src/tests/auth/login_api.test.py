from fastapi.testclient import TestClient

from main import app
from src.core.database import get_db_session
from src.services.auth.errors import AuthFailure
from src.schemas.auth import AuthenticatedUser


class FakeUserAccessService:
    failed_emails = []
    successful_users = []

    def __init__(self, db):
        self.db = db

    def check_login_lockout(self, email):
        return None

    def record_failed_login(self, email):
        self.failed_emails.append(email)
        return None

    def record_successful_login(self, user):
        self.successful_users.append(user)


def _client(monkeypatch):
    FakeUserAccessService.failed_emails = []
    FakeUserAccessService.successful_users = []
    app.dependency_overrides[get_db_session] = lambda: iter([object()])
    monkeypatch.setattr("src.services.auth.auth_controller.UserAccessService", FakeUserAccessService)
    monkeypatch.setattr("src.services.auth.auth_controller.get_supabase_client", lambda: object())
    return TestClient(app)


def test_login_sets_http_only_cookies_and_does_not_return_tokens(monkeypatch):
    user = AuthenticatedUser(id="b381e1f0-8495-4b74-aadd-b5d3b662aafa", email="dev@example.com")

    class SuccessfulLoginService:
        def __init__(self, client):
            pass

        def authenticate(self, credentials):
            assert credentials.email == "dev@example.com"
            return user, "access-secret", "refresh-secret", 3600

    monkeypatch.setattr("src.services.auth.auth_controller.LoginService", SuccessfulLoginService)
    client = _client(monkeypatch)
    try:
        response = client.post("/auth/login", json={"email": " DEV@example.com ", "password": "secret"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"user": user.model_dump(), "expires_in": 3600}
    assert "access-secret" not in response.text
    assert "refresh-secret" not in response.text
    set_cookie_headers = response.headers.get_list("set-cookie")
    assert any("finansys_access_token=access-secret" in value and "httponly" in value.lower() for value in set_cookie_headers)
    assert any("finansys_refresh_token=refresh-secret" in value and "httponly" in value.lower() for value in set_cookie_headers)
    assert FakeUserAccessService.successful_users == [user]


def test_login_returns_generic_authentication_error_and_records_failed_attempt(monkeypatch):
    class RejectedLoginService:
        def __init__(self, client):
            pass

        def authenticate(self, credentials):
            raise AuthFailure(401, "invalid_credentials", "E-mail ou senha inválidos.", "invalid_credentials")

    monkeypatch.setattr("src.services.auth.auth_controller.LoginService", RejectedLoginService)
    client = _client(monkeypatch)
    try:
        response = client.post("/auth/login", json={"email": "dev@example.com", "password": "wrong-password"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    assert response.json()["detail"]["message"] == "E-mail ou senha inválidos."
    assert "wrong-password" not in response.text
    assert FakeUserAccessService.failed_emails == ["dev@example.com"]


def test_login_rejects_invalid_payload_without_exposing_password(monkeypatch):
    client = _client(monkeypatch)
    try:
        response = client.post("/auth/login", json={"email": "invalid", "password": "private-password"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_request"
    assert "private-password" not in response.text
