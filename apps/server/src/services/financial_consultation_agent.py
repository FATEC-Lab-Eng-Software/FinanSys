"""Financial consultation specialist backed by the scoped summary tool."""

from pathlib import Path
from typing import Protocol

from sqlalchemy.orm import Session

from src.services.assistant_tools import AssistantToolContext, build_financial_summary_tool

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "financial-consultation.md"


class HermesCompleter(Protocol):
    def complete(self, messages: list[dict[str, str]]) -> str: ...


class FinancialConsultationAgent:
    def __init__(self, session: Session, user_id: str, hermes_client: HermesCompleter) -> None:
        self._context = AssistantToolContext(session=session, user_id=user_id)
        self._hermes = hermes_client
        self._summary_tool = build_financial_summary_tool()

    def consult(
        self,
        user_messages: list[dict[str, str]],
        start_date: str,
        end_date: str,
    ) -> dict[str, object]:
        try:
            summary = self._summary_tool.execute(
                self._context,
                {"start_date": start_date, "end_date": end_date},
            )
        finally:
            self._context.session.rollback()
        system_prompt = _PROMPT_PATH.read_text(encoding="utf-8").strip()
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(
            message
            for message in user_messages
            if message.get("role") in {"user", "assistant"}
            and isinstance(message.get("content"), str)
        )
        messages.append({"role": "user", "content": f"Resumo financeiro consultado: {summary!r}"})
        answer = self._hermes.complete(messages)
        return {"answer": answer, "summary": summary}
