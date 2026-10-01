from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from src.core.database import get_db_session
from src.schemas.auth import AuthenticatedUser, LoginResponse
from src.services.auth.auth_controller import (
    process_login,
    process_logout,
    process_refresh,
    process_user_lookup,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse:
    return await process_login(request, response, db)


@router.post("/refresh", response_model=LoginResponse)
def refresh_session(request: Request, response: Response) -> LoginResponse | Response:
    return process_refresh(request, response)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, response: Response) -> Response:
    return process_logout(request, response)


@router.get("/me", response_model=AuthenticatedUser)
def get_me(request: Request) -> AuthenticatedUser | Response:
    return process_user_lookup(request)
