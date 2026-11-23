from __future__ import annotations

import base64
import logging
from calendar import monthrange
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from src.schemas.assistant import AssistantArtifact, AssistantBook, AssistantChatResponse, AssistantMessage
from src.services.assistant_action_tools import build_assistant_action_tools
from src.services.assistant_errors import AssistantFailure
from src.services.assistant_hermes_client import HermesClient
from src.services.assistant_planner import OrchestratorAgent
from src.services.assistant_tools import AssistantToolContext
from src.services.book_recommendation_agent import BookRecommendationAgent
from src.services.financial_consultation_agent import FinancialConsultationAgent

logger = logging.getLogger(__name__)


class AssistantCoordinator:
    def __init__(self, session: Session, user_id: str, hermes: HermesClient | None = None) -> None:
        self._context = AssistantToolContext(session=session, user_id=user_id)
        self._hermes = hermes or HermesClient()
        self._orchestrator_agent = OrchestratorAgent(self._hermes)
        self._consultant = FinancialConsultationAgent(session, user_id, self._hermes)
        self._book_recommendations = BookRecommendationAgent()
        self._actions = build_assistant_action_tools()

    def chat(self, messages: list[AssistantMessage]) -> AssistantChatResponse:
        history = [message.model_dump() for message in messages]
        plan = self._orchestrator_agent.plan(history)
        if plan.kind == "final":
            return AssistantChatResponse(message=plan.message or "")
        if plan.action == "email" and not plan.recipient:
            return AssistantChatResponse(message="Qual endereço de email devo usar para enviar o relatório demonstrativo?")
        if plan.agent == "curador_livros":
            try:
                result = self._book_recommendations.recommend(self._context, plan.query or "")
            except AssistantFailure:
                raise
            except ValueError:
                raise AssistantFailure(422, "assistant_book_query_invalid", "Não consegui identificar o tema para buscar livros.") from None
            except Exception:
                logger.warning("assistant_book_search_failed")
                raise AssistantFailure(503, "assistant_book_search_unavailable", "Não foi possível buscar livros agora.") from None
            return AssistantChatResponse(
                message=result["message"],
                books=[AssistantBook.model_validate(book) for book in result["books"]],
            )

        start_date, end_date = self._resolve_period(plan.start_date, plan.end_date)
        try:
            consultation = self._consultant.consult(history, start_date, end_date)
            if plan.action == "consulta":
                return AssistantChatResponse(message=str(consultation["answer"]))

            action_name = "gerar_relatorio_financeiro" if plan.action == "relatorio" else "enviar_relatorio_email"
            arguments: dict[str, Any] = {"summary": consultation["summary"]}
            if plan.action == "email":
                arguments["recipient"] = plan.recipient
            result = self._actions[action_name].execute(self._context, arguments)
        except AssistantFailure:
            raise
        except ValueError:
            raise AssistantFailure(422, "assistant_action_invalid", "Confira o período e os dados informados e tente novamente.") from None
        except Exception:
            logger.warning("assistant_delegation_failed action=%s", plan.action)
            raise AssistantFailure(503, "assistant_action_unavailable", "Não foi possível concluir essa ação agora. Tente novamente.") from None

        artifacts = self._artifacts(result.pop("_artifacts", []))
        message = str(consultation["answer"])
        period = f"{date.fromisoformat(start_date):%d/%m/%Y} a {date.fromisoformat(end_date):%d/%m/%Y}"
        if plan.action == "relatorio":
            message += f"\n\nGerei o relatório financeiro do período {period} em PDF."
        else:
            message += f"\n\nRegistrei o envio demonstrativo do relatório do período {period} para {plan.recipient} no Mailpit local."
        return AssistantChatResponse(message=message, artifacts=artifacts)

    @staticmethod
    def _resolve_period(start_date: str | None, end_date: str | None) -> tuple[str, str]:
        if start_date and end_date:
            return start_date, end_date
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).date()
        return today.replace(day=1).isoformat(), today.replace(day=monthrange(today.year, today.month)[1]).isoformat()

    @staticmethod
    def _artifacts(values: list[Any]) -> list[AssistantArtifact]:
        return [
            AssistantArtifact(
                filename=item.filename,
                content_type=item.content_type,
                content_base64=base64.b64encode(item.content).decode("ascii"),
            )
            for item in values
        ]
