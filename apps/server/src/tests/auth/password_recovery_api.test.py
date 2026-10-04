from fastapi.testclient import TestClient

from main import app
from src.shared.supabase.auth import SupabaseAuthError


class FakeSupabaseClient:
    def __init__(self, failure=None):
        self.failure = failure
        self.recovery_request = None
        self.password_update = None


def _client(monkeypatch, supabase):
    monkeypatch.setattr("src.services.auth.auth_controller.get_supabase_client", lambda: supabase)
    return TestClient(app)


def test_recovery_request_sends_email_and_returns_generic_confirmation(monkeypatch):
    fake = FakeSupabaseClient()
    from src.shared.supabase.auth import SupabaseAuthAdapter

    monkeypatch.setattr(
        SupabaseAuthAdapter,
        "request_password_recovery",
        lambda self, email, redirect_to: setattr(fake, "recovery_request", (email, redirect_to)),
    )
    monkeypatch.setattr(
        "src.services.auth.auth_controller.settings.auth_password_recovery_redirect",
        "http://localhost:3000/password-recovery",
    )
    client = _client(monkeypatch, fake)
    try:
        response = client.post("/auth/password-recovery", json={"email": "  DEV@example.com "})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert "Se houver uma conta" in response.json()["message"]
    assert fake.recovery_request == ("dev@example.com", "http://localhost:3000/password-recovery")


def test_recovery_request_keeps_same_response_for_unknown_account(monkeypatch):
    from src.shared.supabase.auth import SupabaseAuthAdapter

    def unknown(self, email, redirect_to):
        raise SupabaseAuthError(422, "user_not_found")

    monkeypatch.setattr(SupabaseAuthAdapter, "request_password_recovery", unknown)
    client = _client(monkeypatch, FakeSupabaseClient())
    try:
        response = client.post("/auth/password-recovery", json={"email": "unknown@example.com"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    assert "Se houver uma conta" in response.json()["message"]


def test_recovery_rejects_bad_email(monkeypatch):
    client = _client(monkeypatch, FakeSupabaseClient())
    try:
        response = client.post("/auth/password-recovery", json={"email": "invalid"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


def test_recovery_completion_updates_password_with_recovery_token(monkeypatch):
    from src.shared.supabase.auth import SupabaseAuthAdapter

    updated = []
    monkeypatch.setattr(
        SupabaseAuthAdapter,
        "update_password",
        lambda self, access_token, password: updated.append((access_token, password)),
    )
    client = _client(monkeypatch, FakeSupabaseClient())
    try:
        response = client.post(
            "/auth/password-recovery/complete",
            json={"access_token": "recovery-access-token", "new_password": "abcdefgh"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert updated == [("recovery-access-token", "abcdefgh")]


def test_recovery_completion_rejects_password_shorter_than_eight_characters(monkeypatch):
    client = _client(monkeypatch, FakeSupabaseClient())
    try:
        response = client.post(
            "/auth/password-recovery/complete",
            json={"access_token": "recovery-access-token", "new_password": "short!!"},
        )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 422


def test_recovery_completion_accepts_eight_character_password_without_composition_rules(monkeypatch):
    from src.shared.supabase.auth import SupabaseAuthAdapter

    updated = []
    monkeypatch.setattr(
        SupabaseAuthAdapter,
        "update_password",
        lambda self, access_token, password: updated.append((access_token, password)),
    )
    client = _client(monkeypatch, FakeSupabaseClient())
    try:
        response = client.post(
            "/auth/password-recovery/complete",
            json={"access_token": "recovery-access-token", "new_password": "abcdefgh"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert updated == [("recovery-access-token", "abcdefgh")]
