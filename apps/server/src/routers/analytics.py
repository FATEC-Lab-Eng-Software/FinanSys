from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.core.database import get_db_session
from src.routers.transactions import get_current_user
from src.schemas.analytics_schemas import AnalyticsFilters, AnalyticsResponse
from src.schemas.auth import AuthenticatedUser
from src.services.analytics import AnalyticsService, AnalyticsUnavailable

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    filters: Annotated[AnalyticsFilters, Query()],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> AnalyticsResponse | JSONResponse:
    try:
        return AnalyticsService(db).summarize(user.id, filters)
    except AnalyticsUnavailable:
        return JSONResponse(
            status_code=503,
            content={
                "detail": {
                    "code": "analytics_store_unavailable",
                    "message": "Não foi possível carregar as análises financeiras.",
                }
            },
        )
