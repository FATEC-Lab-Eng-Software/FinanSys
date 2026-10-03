from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from src.core.database import get_db_session
from src.schemas.auth import AuthenticatedUser
from src.services.auth.auth_controller import process_user_lookup


def require_authenticated_user(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> AuthenticatedUser:
    result = process_user_lookup(request, db)
    if isinstance(result, Response):
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_session", "message": "Sessão inválida ou expirada."},
        )
    return result
