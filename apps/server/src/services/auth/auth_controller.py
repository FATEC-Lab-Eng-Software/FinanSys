from fastapi import HTTPException, Request, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.core.auth_cookies import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    clear_session_cookies,
    invalid_session_response,
    set_session_cookies,
)
from src.core.security import verify_browser_origin
from src.schemas.auth import AuthenticatedUser, LoginRequest, LoginResponse
from src.services.auth.errors import AuthFailure
from src.services.auth.login_service import LoginService, SessionService
from src.services.auth.user_access_service import UserAccessService
from src.shared.supabase.client import SupabaseConfigurationError, get_supabase_client


def _public_failure(failure: AuthFailure) -> HTTPException:
    return HTTPException(
        status_code=failure.status_code,
        detail={"code": failure.public_code, "message": failure.public_message},
    )


def _internal_failure() -> HTTPException:
    return HTTPException(
        status_code=500,
        detail={"code": "internal_error", "message": "Não foi possível concluir a autenticação."},
    )


def _unavailable_failure() -> HTTPException:
    return HTTPException(
        status_code=503,
        detail={"code": "authentication_unavailable", "message": "Serviço de autenticação indisponível."},
    )


async def process_login(
    request: Request,
    response: Response,
    db: Session,
) -> LoginResponse:
    verify_browser_origin(request)

    try:
        payload = LoginRequest.model_validate(await request.json())
    except (ValidationError, ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_request", "message": "Dados de autenticação inválidos."},
        ) from None

    user_access = UserAccessService(db)
    try:
        user, access, refresh, expires_in = LoginService(get_supabase_client()).authenticate(payload)
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except AuthFailure as failure:
        if failure.audit_outcome == "invalid_credentials":
            try:
                user_access.record_failed_login(payload.email)
            except AuthFailure as store_failure:
                raise _public_failure(store_failure) from None
        raise _public_failure(failure) from None
    except Exception:
        raise _internal_failure() from None

    try:
        user_access.record_successful_login(user)
    except AuthFailure as failure:
        raise _public_failure(failure) from None
    set_session_cookies(response, access, refresh, expires_in)
    return LoginResponse(user=user, expires_in=expires_in)


def process_refresh(request: Request, response: Response) -> LoginResponse | Response:
    verify_browser_origin(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        return invalid_session_response()
    try:
        user, access, next_refresh, expires_in = SessionService(get_supabase_client()).refresh(refresh_token)
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except AuthFailure as failure:
        if failure.status_code == 401:
            return invalid_session_response()
        raise _public_failure(failure) from None
    except Exception:
        raise _internal_failure() from None
    set_session_cookies(response, access, next_refresh, expires_in)
    return LoginResponse(user=user, expires_in=expires_in)


def process_logout(request: Request, response: Response) -> Response:
    verify_browser_origin(request)
    try:
        SessionService(get_supabase_client()).revoke(request.cookies.get(ACCESS_COOKIE))
    except (HTTPException, SupabaseConfigurationError):
        pass
    clear_session_cookies(response)
    response.status_code = 204
    return response


def process_user_lookup(request: Request) -> AuthenticatedUser | Response:
    access_token = request.cookies.get(ACCESS_COOKIE)
    if not access_token:
        return invalid_session_response()
    try:
        return SessionService(get_supabase_client()).current_user(access_token)
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except AuthFailure as failure:
        if failure.status_code == 401:
            return invalid_session_response()
        raise _public_failure(failure) from None
    except Exception:
        raise _internal_failure() from None
