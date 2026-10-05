

from urllib.parse import urlsplit

from fastapi import HTTPException, Request

from src.core.config import settings

def _origin_key(value: str) -> tuple[str, str, int | None] | None:
    try:
        parts = urlsplit(value.strip())
        if (
            parts.scheme.lower() not in {"http", "https"}
            or not parts.hostname
            or parts.username is not None
            or parts.password is not None
            or parts.path not in {"", "/"}
            or parts.query
            or parts.fragment
        ):
            return None
        scheme = parts.scheme.lower()
        host = parts.hostname.lower()
        port = parts.port
        if port == (443 if scheme == "https" else 80):
            port = None
        return (scheme, host, port)
    except ValueError:
        return None

def verify_browser_origin(request: Request) -> None:

    origin = request.headers.get("origin")
    if not origin:

        return

    configured_origins = (*settings.cors_allowed_origins, *settings.auth_trusted_origins)
    allowed = {_origin_key(value) for value in configured_origins}
    request_origin = _origin_key(origin)
    if request_origin is None or request_origin not in allowed:
        raise HTTPException(
            status_code=403,
            detail={"code": "untrusted_origin", "message": "Origem da requisição não autorizada."},
        )
