from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.core.database import get_db_session
from src.routers.transactions import get_current_user
from src.schemas.auth import AuthenticatedUser
from src.schemas.notification import NotificationResponse
from src.services.notifications_service import NotificationFailure, NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[NotificationResponse] | Response:
    try:
        return NotificationService(db).list_for_user(user.id)
    except NotificationFailure as failure:
        return _failure_response(failure)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_notifications(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        NotificationService(db).delete_all(user.id)
    except NotificationFailure as failure:
        return _failure_response(failure)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        NotificationService(db).delete(user.id, notification_id)
    except NotificationFailure as failure:
        return _failure_response(failure)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _failure_response(failure: NotificationFailure) -> JSONResponse:
    return JSONResponse(
        status_code=failure.status_code,
        content={"detail": {"code": failure.code, "message": failure.message}},
    )
