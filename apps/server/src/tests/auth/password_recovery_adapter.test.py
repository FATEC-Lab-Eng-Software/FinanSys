import httpx2

from src.shared.supabase.auth import SupabaseAuthAdapter
from src.shared.supabase.client import SupabaseRestClient


class CaptureTransport(httpx2.BaseTransport):
    def __init__(self):
        self.requests = []

    def handle_request(self, request):
        self.requests.append(request)
        return httpx2.Response(200, json={"id": "user-id"}, request=request)


def test_recovery_adapter_calls_gotrue_recovery_endpoint():
    transport = CaptureTransport()
    client = SupabaseRestClient("http://supabase.test", "anon-key", transport)
    SupabaseAuthAdapter(client).request_password_recovery("person@example.com", "http://localhost:3000/password-recovery")

    request = transport.requests[0]
    assert request.method == "POST"
    assert request.url.path == "/auth/v1/recover"
    assert request.url.params["redirect_to"] == "http://localhost:3000/password-recovery"
    assert request.content == b'{"email":"person@example.com"}'


def test_password_update_uses_recovery_bearer_token():
    transport = CaptureTransport()
    client = SupabaseRestClient("http://supabase.test", "anon-key", transport)
    SupabaseAuthAdapter(client).update_password("recovery-token", "Secure1!Password")

    request = transport.requests[0]
    assert request.method == "PUT"
    assert request.url.path == "/auth/v1/user"
    assert request.headers["authorization"] == "Bearer recovery-token"
    assert request.content == b'{"password":"Secure1!Password"}'
