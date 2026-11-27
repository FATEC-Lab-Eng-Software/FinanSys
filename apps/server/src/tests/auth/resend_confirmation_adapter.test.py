import httpx2

from src.shared.supabase.auth import SupabaseAuthAdapter
from src.shared.supabase.client import SupabaseRestClient


class CaptureTransport(httpx2.BaseTransport):
    def __init__(self):
        self.requests = []

    def handle_request(self, request):
        self.requests.append(request)
        return httpx2.Response(200, json={}, request=request)


def test_resend_confirmation_adapter_calls_signup_resend_endpoint():
    transport = CaptureTransport()
    client = SupabaseRestClient("http://supabase.test", "anon-key", transport)
    SupabaseAuthAdapter(client).resend_signup_confirmation("person@example.com")

    request = transport.requests[0]
    assert request.method == "POST"
    assert request.url.path == "/auth/v1/resend"
    assert request.content == b'{"type":"signup","email":"person@example.com"}'
