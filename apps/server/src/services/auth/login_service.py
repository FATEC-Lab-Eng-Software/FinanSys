from typing import Any

from src.schemas.auth import AuthenticatedUser, LoginRequest
from src.services.auth.errors import AuthFailure, classify_provider_error
from src.shared.supabase.auth import SupabaseAuthAdapter, SupabaseAuthError

def _provider_user(value: Any) -> AuthenticatedUser | None:
    if not isinstance(value, dict) or not value.get("id"):
        return None
    email = value.get("email")
    metadata = value.get("user_metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    first_name = metadata.get("first_name") or metadata.get("given_name")
    last_name = metadata.get("last_name") or metadata.get("family_name")
    full_name = metadata.get("full_name") or metadata.get("name")
    if isinstance(full_name, str):
        name_parts = full_name.strip().split(maxsplit=1)
        if name_parts:
            first_name = first_name or name_parts[0]
        if len(name_parts) == 2:
            last_name = last_name or name_parts[1]
    return AuthenticatedUser(
        id=str(value["id"]),
        email=email if isinstance(email, str) else None,
        first_name=first_name if isinstance(first_name, str) else None,
        last_name=last_name if isinstance(last_name, str) else None,
    )

def _token(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None

def _expires_in(value: Any) -> int:
    try:
        return max(1, min(int(value or 3600), 24 * 60 * 60))
    except (TypeError, ValueError):
        return 3600

class LoginService:
    def __init__(self, supabase_client: Any) -> None:
        self._auth = SupabaseAuthAdapter(supabase_client)

    def authenticate(self, credentials: LoginRequest) -> tuple[AuthenticatedUser, str, str, int]:
        try:
            result = self._auth.login(credentials.email, credentials.password)
        except SupabaseAuthError as error:
            raise classify_provider_error(error) from None

        user = _provider_user(result.get("user"))
        access_token = _token(result.get("access_token"))
        refresh_token = _token(result.get("refresh_token"))
        if not user or not access_token or not refresh_token:
            raise AuthFailure(502, "authentication_failed", "Não foi possível concluir a autenticação.", "provider_failure")

        expires_in = _expires_in(result.get("expires_in"))
        return (
            user,
            access_token,
            refresh_token,
            expires_in,
        )

class SessionService:

    def __init__(self, supabase_client: Any) -> None:
        self._auth = SupabaseAuthAdapter(supabase_client)

    def refresh(self, refresh_token: str) -> tuple[AuthenticatedUser, str, str, int]:
        try:
            result = self._auth.refresh(refresh_token)
        except SupabaseAuthError as error:
            status = error.status
            if status == 401 or error.code in {
                "refresh_token_not_found",
                "invalid_refresh_token",
                "session_not_found",
                "session_expired",
                "invalid_token",
                "bad_jwt",
            }:
                raise AuthFailure(401, "invalid_session", "Sessão inválida ou expirada.", "invalid_session") from None
            failure = classify_provider_error(error)
            if failure.status_code == 401:
                raise AuthFailure(401, "invalid_session", "Sessão inválida ou expirada.", "invalid_session") from None
            raise failure from None

        user = _provider_user(result.get("user"))
        access_token = _token(result.get("access_token"))
        next_refresh_token = _token(result.get("refresh_token"))
        if not user or not access_token or not next_refresh_token:
            raise AuthFailure(401, "invalid_session", "Sessão inválida ou expirada.", "invalid_session")
        return (
            user,
            access_token,
            next_refresh_token,
            _expires_in(result.get("expires_in")),
        )

    def current_user(self, access_token: str) -> AuthenticatedUser:
        try:
            result = self._auth.get_user(access_token)
        except SupabaseAuthError as error:
            status = getattr(error, "status", getattr(error, "status_code", None))
            try:
                status = int(status) if status is not None else None
            except (TypeError, ValueError):
                status = None
            if status == 401 or str(getattr(error, "code", "")).lower() in {
                "user_not_found", "session_not_found", "session_expired", "invalid_token"
            }:
                raise AuthFailure(401, "invalid_session", "Sessão inválida ou expirada.", "invalid_session") from None
            failure = classify_provider_error(error)
            if failure.status_code in {502, 503}:
                raise failure from None
            raise AuthFailure(401, "invalid_session", "Sessão inválida ou expirada.", "invalid_session") from None

        user = _provider_user(result)
        if not user:
            raise AuthFailure(401, "invalid_session", "Sessão inválida ou expirada.", "invalid_session")
        return user

    def revoke(self, access_token: str | None) -> None:

        if not access_token:
            return
        try:
            self._auth.logout(access_token)
        except Exception:

            return
