from sqlalchemy.orm import Session

from src.schemas.assistant import AssistantChatResponse, AssistantMessage
from src.services.assistant_orchestrator import AssistantCoordinator


class AssistantService:
    def __init__(self, session: Session, user_id: str) -> None:
        self._coordinator = AssistantCoordinator(session, user_id)

    def chat(self, messages: list[AssistantMessage]) -> AssistantChatResponse:
        return self._coordinator.chat(messages)
