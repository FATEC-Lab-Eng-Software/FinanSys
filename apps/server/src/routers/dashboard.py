from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.core.database import get_db_session
from src.routers.transactions import get_current_user
from src.schemas.auth import AuthenticatedUser
from src.schemas.dashboard import DashboardResponse
from src.services.dashboard import DashboardFailure, DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> DashboardResponse | Response:
    try:
        return DashboardService(db).get(user.id)
    except DashboardFailure as failure:
        return JSONResponse(
            status_code=failure.status_code,
            content={"detail": {"code": failure.code, "message": failure.message}},
        )