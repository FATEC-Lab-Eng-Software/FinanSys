import base64
import binascii
import json
from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from fastapi import HTTPException, Request, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from src.core.config import settings
from src.core.auth_cookies import (
    ACCESS_COOKIE,
    REFRESH_COOKIE,
    clear_session_cookies,
    invalid_session_response,
    set_session_cookies,
)
from src.core.security import verify_browser_origin
from src.schemas.auth import (
    AuthenticatedUser,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    PasswordRecoveryCompleteRequest,
    PasswordRecoveryRequest,
)
from src.services.auth.errors import AuthFailure
from src.services.auth.login_service import LoginService, SessionService
from src.services.auth.user_access_service import UserAccessService
from src.shared.supabase.client import SupabaseConfigurationError, get_supabase_client
from src.shared.supabase.auth import SupabaseAuthAdapter, SupabaseAuthError


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


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _locked_response(locked_until: datetime) -> HTTPException:
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)
    retry_after = max(1, ceil((locked_until - utc_now()).total_seconds()))
    return HTTPException(
        status_code=423,
        detail={
            "code": "account_temporarily_locked",
            "message": "Acesso temporariamente bloqueado por excesso de tentativas.",
            "locked_until": locked_until.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        headers={"Retry-After": str(retry_after)},
    )

async def process_register(request: Request, db: Session) -> dict[str, str]:
    verify_browser_origin(request)
    try:
        payload = RegisterRequest.model_validate(await request.json())
    except (ValidationError, ValueError, TypeError):
        raise HTTPException(status_code=422, detail={"code": "invalid_request", "message": "Dados de cadastro inválidos."}) from None

    try:
        SupabaseAuthAdapter(get_supabase_client()).register(payload.email, payload.password, payload.name)
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except SupabaseAuthError as error:
        if error.status in {400, 409} or error.code in {"user_already_exists", "email_exists"}:
            raise HTTPException(status_code=409, detail={"code": "email_already_registered", "message": "Este e-mail já está cadastrado."}) from None
        raise _public_failure(AuthFailure(502, "registration_failed", "Não foi possível concluir o cadastro.", "provider_failure")) from None
    except Exception:
        raise _internal_failure() from None
    return {"message": "Cadastro realizado com sucesso."}


def _access_token_subject(access_token: str) -> str | None:
    parts = access_token.split(".")
    if len(parts) != 3:
        return None
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        payload_data = json.loads(base64.urlsafe_b64decode(payload))
        if not isinstance(payload_data, dict):
            return None
        subject = payload_data.get("sub")
        return str(UUID(subject)) if isinstance(subject, str) else None
    except (ValueError, TypeError, binascii.Error, json.JSONDecodeError):
        return None


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
        locked_until = user_access.check_login_lockout(payload.email)
    except AuthFailure as failure:
        raise _public_failure(failure) from None
    except Exception:
        raise _internal_failure() from None
    if locked_until is not None:
        raise _locked_response(locked_until)

    try:
        user, access, refresh, expires_in = LoginService(get_supabase_client()).authenticate(payload)
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except AuthFailure as failure:
        if failure.audit_outcome == "invalid_credentials":
            try:
                locked_until = user_access.record_failed_login(payload.email)
            except AuthFailure as store_failure:
                raise _public_failure(store_failure) from None
            if locked_until is not None:
                raise _locked_response(locked_until) from None
        raise _public_failure(failure) from None
    except Exception:
        raise _internal_failure() from None

    try:
        user_access.record_successful_login(user)
    except AuthFailure as failure:
        raise _public_failure(failure) from None
    set_session_cookies(response, access, refresh, expires_in)
    return LoginResponse(user=user, expires_in=expires_in)


def process_refresh(request: Request, response: Response, db: Session) -> LoginResponse | Response:
    verify_browser_origin(request)
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    access_token = request.cookies.get(ACCESS_COOKIE)
    if not refresh_token:
        return invalid_session_response()
    try:
        session_service = SessionService(get_supabase_client())
        user = None
        if access_token:
            try:
                user = session_service.current_user(access_token)
            except AuthFailure as failure:
                if failure.status_code != 401:
                    raise
        subject = user.id if user is not None else _access_token_subject(access_token or "")
        user_access = UserAccessService(db)
        if subject is None or not user_access.is_session_active(subject, utc_now()):
            return invalid_session_response()
        refreshed_user, access, next_refresh, expires_in = session_service.refresh(refresh_token)
        if refreshed_user.id != subject:
            return invalid_session_response()
        if not user_access.check_session_activity(refreshed_user.id, utc_now()):
            return invalid_session_response()
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except AuthFailure as failure:
        if failure.status_code == 401:
            return invalid_session_response()
        raise _public_failure(failure) from None
    except Exception:
        raise _internal_failure() from None
    set_session_cookies(response, access, next_refresh, expires_in)
    return LoginResponse(user=refreshed_user, expires_in=expires_in)


def process_logout(request: Request, response: Response) -> Response:
    verify_browser_origin(request)
    try:
        SessionService(get_supabase_client()).revoke(request.cookies.get(ACCESS_COOKIE))
    except (HTTPException, SupabaseConfigurationError):
        pass
    clear_session_cookies(response)
    response.status_code = 204
    return response


def process_user_lookup(request: Request, db: Session) -> AuthenticatedUser | Response:
    access_token = request.cookies.get(ACCESS_COOKIE)
    if not access_token:
        return invalid_session_response()
    try:
        user = SessionService(get_supabase_client()).current_user(access_token)
        if not UserAccessService(db).check_session_activity(user.id, utc_now()):
            return invalid_session_response()
        return user
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except AuthFailure as failure:
        if failure.status_code == 401:
            return invalid_session_response()
        raise _public_failure(failure) from None
    except Exception:
        raise _internal_failure() from None


def process_password_recovery_request(request: Request, payload: PasswordRecoveryRequest) -> dict[str, str]:
    verify_browser_origin(request)
    # Keep responses identical for existing and unknown accounts.
    try:
        SupabaseAuthAdapter(get_supabase_client()).request_password_recovery(
            payload.email, settings.auth_password_recovery_redirect
        )
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except SupabaseAuthError as error:
        if error.status == 429:
            # Preserve privacy while honoring provider throttling.
            pass
        elif error.status is not None and error.status >= 500:
            raise _unavailable_failure() from None
    except Exception:
        raise _internal_failure() from None
    return {"message": "Se houver uma conta associada, enviaremos instruções para redefinir a senha."}


def process_password_recovery_complete(
    request: Request, payload: PasswordRecoveryCompleteRequest
) -> dict[str, str]:
    verify_browser_origin(request)
    try:
        SupabaseAuthAdapter(get_supabase_client()).update_password(payload.access_token, payload.new_password)
    except SupabaseConfigurationError:
        raise _unavailable_failure() from None
    except SupabaseAuthError as error:
        if error.status == 401 or error.code in {"invalid_token", "session_not_found", "session_expired"}:
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_recovery_link", "message": "O link de recuperação é inválido ou expirou."},
            ) from None
        if error.code == "weak_password":
            raise HTTPException(
                status_code=422,
                detail={"code": "weak_password", "message": "A senha não atende aos requisitos de segurança."},
            ) from None
        raise _unavailable_failure() from None
    except Exception:
        raise _internal_failure() from None
    return {"message": "Senha redefinida com sucesso."}
