from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.core.database import get_db_session
from src.schemas.auth import AuthenticatedUser
from src.schemas.goals_schemas import (
    GoalCreate,
    GoalFilters,
    GoalProgressResponse,
    GoalResponse,
    GoalUpdate,
)
from src.routers.transactions import get_current_user
from src.services.goals_service import GoalFailure, GoalService

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> GoalResponse | Response:
    try:
        return GoalService(db).create(user.id, payload)
    except GoalFailure as failure:
        return _failure_response(failure)


@router.get("", response_model=list[GoalResponse])
def list_goals(
    filters: Annotated[GoalFilters, Query()],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[GoalResponse] | Response:
    try:
        return GoalService(db).list_for_user(user.id, filters)
    except GoalFailure as failure:
        return _failure_response(failure)


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: int,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> GoalResponse | Response:
    try:
        return GoalService(db).get(user.id, goal_id)
    except GoalFailure as failure:
        return _failure_response(failure)


@router.get("/{goal_id}/progress", response_model=GoalProgressResponse)
def get_goal_progress(
    goal_id: int,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> GoalProgressResponse | Response:
    try:
        return GoalService(db).get_progress(user.id, goal_id)
    except GoalFailure as failure:
        return _failure_response(failure)


@router.patch("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: int,
    payload: GoalUpdate,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> GoalResponse | Response:
    try:
        return GoalService(db).update(user.id, goal_id, payload)
    except GoalFailure as failure:
        return _failure_response(failure)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        GoalService(db).delete(user.id, goal_id)
    except GoalFailure as failure:
        return _failure_response(failure)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _failure_response(failure: GoalFailure) -> JSONResponse:
    return JSONResponse(
        status_code=failure.status_code,
        content={"detail": {"code": failure.code, "message": failure.message}},
    )