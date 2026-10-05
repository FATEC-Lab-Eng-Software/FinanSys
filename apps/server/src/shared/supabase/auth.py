

import re
from typing import Any

import httpx2

from src.shared.supabase.client import SupabaseRestClient

_SAFE_CODE = re.compile(r"^[a-zA-Z0-9_]{1,80}$")

class SupabaseAuthError(Exception):

    def __init__(self, status: int | None, code: str = "") -> None:
        super().__init__("Supabase Auth request failed")
        self.status = status
        self.code = code.lower() if _SAFE_CODE.fullmatch(code or "") else ""

class SupabaseAuthAdapter:
    def __init__(self, client: SupabaseRestClient) -> None:
        self._client = client

    def login(self, email: str, password: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/v1/token?grant_type=password",
            json={"email": email, "password": password},
        )

    def register(self, email: str, password: str, name: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/v1/signup",
            json={"email": email, "password": password, "data": {"full_name": name}},
        )

    def refresh(self, refresh_token: str) -> dict[str, Any]:
        return self._request(
            "POST",
            "/auth/v1/token?grant_type=refresh_token",
            json={"refresh_token": refresh_token},
        )

    def get_user(self, access_token: str) -> dict[str, Any]:
        return self._request("GET", "/auth/v1/user", access_token=access_token)

    def logout(self, access_token: str) -> None:
        self._request(
            "POST",
            "/auth/v1/logout?scope=local",
            access_token=access_token,
            expect_json=False,
        )

    def request_password_recovery(self, email: str, redirect_to: str) -> None:
        from urllib.parse import quote

        redirect = quote(redirect_to, safe="")
        self._request(
            "POST",
            f"/auth/v1/recover?redirect_to={redirect}",
            json={"email": email},
            expect_json=False,
        )

    def update_password(self, access_token: str, password: str) -> dict[str, Any]:
        return self._request(
            "PUT",
            "/auth/v1/user",
            json={"password": password},
            access_token=access_token,
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        access_token: str | None = None,
        expect_json: bool = True,
    ) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, json=json, access_token=access_token)
        except httpx2.TimeoutException:
            raise SupabaseAuthError(None, "request_timeout") from None
        except httpx2.RequestError:
            raise SupabaseAuthError(None, "network_error") from None

        if not 200 <= response.status_code < 300:
            code = ""
            try:
                body = response.json()
                if isinstance(body, dict):
                    for candidate in (body.get("error_code"), body.get("code")):
                        if isinstance(candidate, str) and _SAFE_CODE.fullmatch(candidate):
                            code = candidate
                            break
            except (ValueError, TypeError):
                pass

            raise SupabaseAuthError(response.status_code, code)

        if not expect_json:
            return {}
        try:
            body = response.json()
        except (ValueError, TypeError):
            raise SupabaseAuthError(502, "malformed_provider_response") from None
        if not isinstance(body, dict):
            raise SupabaseAuthError(502, "malformed_provider_response")
        return body

