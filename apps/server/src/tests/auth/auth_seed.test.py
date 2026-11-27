from src.core.config import settings
from src.seeds.auth.seed import SEEDED_PASSWORD, _ensure_seed_accounts


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeClient:
    def __init__(self):
        self.requests = []

    def post(self, url, *, headers, json):
        self.requests.append(("POST", url, json))
        return FakeResponse({"id": "seed-user-id", "email": json["email"]})

    def put(self, url, *, headers, json):
        self.requests.append(("PUT", url, json))
        return FakeResponse({"id": url.rsplit("/", 1)[1], "email": "cliente@finansys.test"})


def test_seed_creates_users_without_email_invite(monkeypatch):
    monkeypatch.setattr(settings, "supabase_url", "http://supabase-auth.local")
    client = FakeClient()
    profile = {
        "role": "client",
        "email": "miguel.ferreira@finansys.test",
        "first_name": "Miguel",
        "last_name": "Ferreira",
    }

    _ensure_seed_accounts(client, {}, [], [profile])

    method, url, payload = client.requests[0]
    assert method == "POST"
    assert url == "http://supabase-auth.local/auth/v1/admin/users"
    assert payload["email"] == profile["email"]
    assert payload["password"] == SEEDED_PASSWORD
    assert payload["email_confirm"] is True
    assert payload["user_metadata"] == {"first_name": "Miguel", "last_name": "Ferreira"}
    assert all("/invite" not in request_url for _, request_url, _ in client.requests)
