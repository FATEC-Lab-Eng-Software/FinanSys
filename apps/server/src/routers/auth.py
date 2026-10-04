from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from src.core.database import get_db_session
from src.schemas.auth import (
    AuthenticatedUser,
    LoginResponse,
    PasswordRecoveryCompleteRequest,
    PasswordRecoveryRequest,
)
from src.services.auth.auth_controller import (
    process_login,
    process_logout,
    process_password_recovery_complete,
    process_password_recovery_request,
    process_refresh,
    process_user_lookup,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/password-recovery", status_code=status.HTTP_202_ACCEPTED)
async def request_password_recovery(request: Request) -> dict[str, str]:
    from pydantic import ValidationError

    try:
        payload = PasswordRecoveryRequest.model_validate(await request.json())
    except (ValidationError, ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_request", "message": "Informe um endereço de e-mail válido."},
        ) from None
    return process_password_recovery_request(request, payload)


@router.post("/password-recovery/complete")
async def complete_password_recovery(request: Request) -> dict[str, str]:
    from pydantic import ValidationError

    try:
        payload = PasswordRecoveryCompleteRequest.model_validate(await request.json())
    except (ValidationError, ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_request", "message": "Os dados para redefinição de senha são inválidos."},
        ) from None
    return process_password_recovery_complete(request, payload)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse:
    return await process_login(request, response, db)


@router.post("/refresh", response_model=LoginResponse)
def refresh_session(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse | Response:
    return process_refresh(request, response, db)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response) -> Response:
    return process_logout(request, response)


@router.get("/me", response_model=AuthenticatedUser)
def get_me(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> AuthenticatedUser | Response:
    return process_user_lookup(request, db)
