from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from src.core.auth_dependencies import require_authenticated_user
from src.core.security import verify_browser_origin
from src.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from src.schemas.auth import AuthenticatedUser
from src.services.assistant_service import AssistantFailure, AssistantService

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantChatResponse)
def chat(
    payload: AssistantChatRequest,
    request: Request,
    _: Annotated[AuthenticatedUser, Depends(require_authenticated_user)],
) -> AssistantChatResponse | JSONResponse:
    verify_browser_origin(request)
    try:
        return AssistantChatResponse(message=AssistantService().chat(payload.messages))
    except AssistantFailure as failure:
        return JSONResponse(
            status_code=failure.status_code,
            content={"detail": {"code": failure.code, "message": failure.message}},
        )
