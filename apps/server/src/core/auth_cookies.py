from fastapi.responses import JSONResponse
from starlette.responses import Response

from src.core.config import settings

ACCESS_COOKIE = "finansys_access_token"
REFRESH_COOKIE = "finansys_refresh_token"
_REFRESH_MAX_AGE_SECONDS = 60 * 60 * 24 * 30

def _cookie_options() -> dict[str, str | bool]:
    same_site = settings.auth_cookie_samesite
    if same_site not in {"lax", "strict", "none"}:
        same_site = "lax"
    return {
        "httponly": True,
        "secure": settings.auth_cookie_secure or same_site == "none",
        "samesite": same_site,
    }

def set_session_cookies(response: Response, access: str, refresh: str, expires_in: int) -> None:
    options = _cookie_options()
    response.set_cookie(ACCESS_COOKIE, access, max_age=_REFRESH_MAX_AGE_SECONDS, path="/", **options)
    response.set_cookie(
        REFRESH_COOKIE,
        refresh,
        max_age=_REFRESH_MAX_AGE_SECONDS,
        path="/auth",
        **options,
    )

def clear_session_cookies(response: Response) -> None:
    options = _cookie_options()
    response.delete_cookie(ACCESS_COOKIE, path="/", **options)
    response.delete_cookie(REFRESH_COOKIE, path="/auth", **options)

def invalid_session_response() -> JSONResponse:
    response = JSONResponse(
        status_code=401,
        content={"detail": {"code": "invalid_session", "message": "Sessão inválida ou expirada."}},
    )
    clear_session_cookies(response)
    return response
