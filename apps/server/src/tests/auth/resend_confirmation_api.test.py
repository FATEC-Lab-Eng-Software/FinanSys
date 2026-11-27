from fastapi.testclient import TestClient

from main import app
from src.shared.supabase.auth import SupabaseAuthError


def _client(monkeypatch, resend):
    from src.shared.supabase.auth import SupabaseAuthAdapter

    monkeypatch.setattr(SupabaseAuthAdapter, "resend_signup_confirmation", resend, raising=False)
    return TestClient(app)


def test_resend_confirmation_returns_generic_response(monkeypatch):
    requests = []

    def resend(self, email):
        requests.append(email)

    client = _client(monkeypatch, resend)
    response = client.post("/auth/resend-confirmation", json={"email": "  PERSON@example.com "})

    assert response.status_code == 202
    assert "Se esta conta ainda precisar de confirmação" in response.json()["message"]
    assert requests == ["person@example.com"]


def test_resend_confirmation_returns_rate_limit_response(monkeypatch):
    def resend(self, email):
        raise SupabaseAuthError(429, "over_email_send_rate_limit")

    client = _client(monkeypatch, resend)
    response = client.post("/auth/resend-confirmation", json={"email": "person@example.com"})

    assert response.status_code == 429
    assert response.json()["detail"]["code"] == "email_rate_limited"


def test_resend_confirmation_rejects_invalid_email(monkeypatch):
    client = _client(monkeypatch, lambda self, email: None)
    response = client.post("/auth/resend-confirmation", json={"email": "invalid"})

    assert response.status_code == 422


def test_resend_confirmation_returns_service_unavailable_for_provider_failure(monkeypatch):
    def resend(self, email):
        raise SupabaseAuthError(503, "internal_error")

    client = _client(monkeypatch, resend)
    response = client.post("/auth/resend-confirmation", json={"email": "person@example.com"})

    assert response.status_code == 503
