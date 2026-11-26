from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from src.core.auth_dependencies import require_authenticated_user
from src.core.database import get_db_session
from src.core.security import verify_browser_origin
from src.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from src.schemas.auth import AuthenticatedUser
from src.services.assistant_errors import AssistantFailure
from src.services.assistant_service import AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantChatResponse)
def chat(
    payload: AssistantChatRequest,
    request: Request,
    user: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
    db: Annotated[Session, Depends(get_db_session)],
) -> AssistantChatResponse | JSONResponse:
    verify_browser_origin(request)
    try:
        return AssistantService(db, user.id).chat(payload.messages)
    except AssistantFailure as failure:
        return JSONResponse(
            status_code=failure.status_code,
            content={"detail": {"code": failure.code, "message": failure.message}},
        )
