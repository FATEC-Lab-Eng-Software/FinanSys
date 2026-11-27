from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.core.auth_dependencies import require_authenticated_user
from src.core.database import get_db_session
from src.repositories.auth import UserRepository
from src.schemas.admin import AdminClientListResponse, AdminClientResponse, AdminClientStatusUpdate
from src.schemas.admin_overview import AdminOverviewResponse
from src.schemas.auth import AuthenticatedUser

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_user(
    user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> AuthenticatedUser:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail={"code": "admin_required", "message": "Acesso restrito a administradores."})
    return user


@router.get("/overview", response_model=AdminOverviewResponse)
def get_overview(
    _: Annotated[AuthenticatedUser, Depends(require_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> AdminOverviewResponse:
    return AdminOverviewResponse(**UserRepository(db).client_overview())


@router.get("/clients", response_model=AdminClientListResponse)
def list_clients(
    _: Annotated[AuthenticatedUser, Depends(require_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
    search: Annotated[str, Query(max_length=120)] = "",
    active: bool | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
) -> AdminClientListResponse:
    repository = UserRepository(db)
    results = repository.list_clients(search=search, active=active, limit=page_size + 1, offset=(page - 1) * page_size)
    return AdminClientListResponse(items=results[:page_size], page=page, page_size=page_size, has_more=len(results) > page_size)


@router.patch("/clients/{user_id}/status", response_model=AdminClientResponse)
def update_client_status(
    user_id: UUID,
    payload: AdminClientStatusUpdate,
    _: Annotated[AuthenticatedUser, Depends(require_admin_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> AdminClientResponse:
    user = UserRepository(db).update_client_status(user_id, payload.is_active)
    if user is None:
        raise HTTPException(status_code=404, detail={"code": "client_not_found", "message": "Cliente não encontrado."})
    return AdminClientResponse.model_validate(user)
