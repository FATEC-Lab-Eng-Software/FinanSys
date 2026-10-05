from types import SimpleNamespace

import pytest

from src.schemas.auth import LoginRequest
from src.services.auth.errors import AuthFailure
from src.services.auth.login_service import LoginService
from src.shared.supabase.auth import SupabaseAuthError


class FakeAuthAdapter:
    def __init__(self, client):
        self.client = client

    def login(self, email, password):
        if self.client.error:
            raise self.client.error
        return self.client.result


def test_login_service_returns_user_and_session_tokens(monkeypatch):
    result = {
        "user": {
            "id": "b381e1f0-8495-4b74-aadd-b5d3b662aafa",
            "email": "dev@example.com",
            "user_metadata": {"full_name": "Dev Tester"},
        },
        "access_token": "access-secret",
        "refresh_token": "refresh-secret",
        "expires_in": 7200,
    }
    monkeypatch.setattr("src.services.auth.login_service.SupabaseAuthAdapter", FakeAuthAdapter)

    user, access, refresh, expires_in = LoginService(SimpleNamespace(error=None, result=result)).authenticate(
        LoginRequest(email=" DEV@example.com ", password="password")
    )

    assert user.id == result["user"]["id"]
    assert user.email == "dev@example.com"
    assert user.first_name == "Dev"
    assert user.last_name == "Tester"
    assert (access, refresh, expires_in) == ("access-secret", "refresh-secret", 7200)


def test_login_service_rejects_incomplete_provider_response(monkeypatch):
    monkeypatch.setattr("src.services.auth.login_service.SupabaseAuthAdapter", FakeAuthAdapter)
    client = SimpleNamespace(
        error=None,
        result={"user": {"id": "user-id", "email": "dev@example.com"}, "access_token": "access"},
    )

    with pytest.raises(AuthFailure) as raised:
        LoginService(client).authenticate(LoginRequest(email="dev@example.com", password="password"))

    assert raised.value.status_code == 502
    assert raised.value.audit_outcome == "provider_failure"


def test_login_service_sanitizes_invalid_credentials(monkeypatch):
    monkeypatch.setattr("src.services.auth.login_service.SupabaseAuthAdapter", FakeAuthAdapter)
    error = SupabaseAuthError(400, "invalid_credentials")
    client = SimpleNamespace(error=error, result=None)

    with pytest.raises(AuthFailure) as raised:
        LoginService(client).authenticate(LoginRequest(email="dev@example.com", password="password"))

    assert raised.value.status_code == 401
    assert raised.value.public_message == "E-mail ou senha inválidos."
    assert "private provider detail" not in raised.value.public_message

