import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.core.database import get_db_session
from src.schemas.auth import AuthenticatedUser
from src.schemas.transactions_schemas import (
    TransactionCreate,
    TransactionFilters,
    TransactionResponse,
    TransactionUpdate,
)
from src.services.auth.auth_controller import process_user_lookup
from src.services.transactions import TransactionFailure, TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db_session)],
) -> AuthenticatedUser:
    result = process_user_lookup(request, db)
    if isinstance(result, Response):
        raise HTTPException(
            status_code=result.status_code or status.HTTP_401_UNAUTHORIZED,
            detail=_read_detail(result),
        )
    return result


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> TransactionResponse | Response:
    try:
        return TransactionService(db).create(user.id, payload)
    except TransactionFailure as failure:
        return _failure_response(failure)


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    filters: Annotated[TransactionFilters, Query()],
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> list[TransactionResponse] | Response:
    try:
        return TransactionService(db).list_for_user(user.id, filters)
    except TransactionFailure as failure:
        return _failure_response(failure)


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> TransactionResponse | Response:
    try:
        return TransactionService(db).get(user.id, transaction_id)
    except TransactionFailure as failure:
        return _failure_response(failure)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> TransactionResponse | Response:
    try:
        return TransactionService(db).update(user.id, transaction_id, payload)
    except TransactionFailure as failure:
        return _failure_response(failure)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> Response:
    try:
        TransactionService(db).delete(user.id, transaction_id)
    except TransactionFailure as failure:
        return _failure_response(failure)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _failure_response(failure: TransactionFailure) -> JSONResponse:
    return JSONResponse(
        status_code=failure.status_code,
        content={"detail": {"code": failure.code, "message": failure.message}},
    )


def _read_detail(response: Response) -> object:
    try:
        return json.loads(response.body).get("detail")
    except (ValueError, TypeError, AttributeError):
        return None