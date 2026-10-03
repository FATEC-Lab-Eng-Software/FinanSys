

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx2

from src.core.config import settings

class SupabaseConfigurationError(RuntimeError):
    pass

@dataclass(frozen=True)
class SupabaseRestClient:
    base_url: str
    api_key: str
    transport: httpx2.BaseTransport
    timeout: float = 10.0

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        access_token: str | None = None,
    ) -> httpx2.Response:

        headers = {"apikey": self.api_key}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        with httpx2.Client(
            transport=_SharedTransport(self.transport),
            timeout=self.timeout,
            follow_redirects=False,
        ) as request_client:
            return request_client.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                json=json,
            )

class _SharedTransport(httpx2.BaseTransport):

    def __init__(self, shared: httpx2.BaseTransport) -> None:
        self._shared = shared

    def handle_request(self, request: httpx2.Request) -> httpx2.Response:
        return self._shared.handle_request(request)

    def close(self) -> None:

        return None

@lru_cache(maxsize=1)
def get_supabase_client() -> SupabaseRestClient:

    url = settings.supabase_url
    key = settings.supabase_public_key
    if not url or not key:
        raise SupabaseConfigurationError(
            "SUPABASE_URL and a public Supabase key (SUPABASE_ANON_KEY, SUPABASE_PUBLISHABLE_KEY, or ANON_KEY) are required"
        )
    try:
        parsed_url = httpx2.URL(url)
    except (TypeError, ValueError):
        raise SupabaseConfigurationError("SUPABASE_URL is malformed") from None
    if parsed_url.scheme not in {"https", "http"} or not parsed_url.host:
        raise SupabaseConfigurationError("SUPABASE_URL must use HTTP or HTTPS")

    try:
        return SupabaseRestClient(base_url=url, api_key=key, transport=httpx2.HTTPTransport())
    except Exception as error:
        raise SupabaseConfigurationError("Supabase HTTP client initialization failed") from error

def close_supabase_client() -> None:

    if get_supabase_client.cache_info().currsize:
        client = get_supabase_client()
        client.transport.close()
        get_supabase_client.cache_clear()

