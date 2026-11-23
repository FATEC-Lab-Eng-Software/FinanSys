import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator

from src.services.assistant_errors import AssistantFailure
from src.services.assistant_hermes_client import HermesClient

_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "assistant-system.md"


class AssistantPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["final", "delegate"]
    message: str | None = None
    agent: Literal["consultor_financeiro", "curador_livros"] | None = None
    action: Literal["consulta", "relatorio", "email", "buscar_livros"] | None = None
    start_date: str | None = None
    end_date: str | None = None
    recipient: str | None = None
    query: str | None = None

    @model_validator(mode="after")
    def validate_plan(self) -> "AssistantPlan":
        if self.kind == "final":
            if not self.message or not self.message.strip() or any((self.agent, self.action, self.start_date, self.end_date, self.recipient, self.query)):
                raise ValueError("Resposta final inválida")
            self.message = self.message.strip()
            return self
        if self.message is not None:
            raise ValueError("Delegação inválida")
        if self.agent == "curador_livros":
            if (
                self.action != "buscar_livros"
                or not self.query
                or not self.query.strip()
                or len(self.query) > 180
                or any((self.start_date, self.end_date, self.recipient))
            ):
                raise ValueError("Busca de livros inválida")
            self.query = self.query.strip()
            return self
        if self.agent != "consultor_financeiro" or self.action not in {"consulta", "relatorio", "email"} or self.query is not None:
            raise ValueError("Delegação inválida")
        if (self.start_date is None) != (self.end_date is None):
            raise ValueError("O período precisa estar completo")
        if self.recipient is not None:
            self.recipient = self.recipient.strip()
        if self.action != "email" and self.recipient is not None:
            raise ValueError("Destinatário inesperado")
        return self


class OrchestratorAgent:
    def __init__(self, hermes: HermesClient) -> None:
        self._hermes = hermes

    def plan(self, messages: list[dict[str, str]]) -> AssistantPlan:
        try:
            system_prompt = _PROMPT_PATH.read_text(encoding="utf-8").strip()
            content = self._hermes.complete([{"role": "system", "content": system_prompt}, *messages])
            if content.startswith("```"):
                content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            decision = json.loads(content)
            return AssistantPlan.model_validate(decision)
        except OSError:
            raise AssistantFailure(503, "assistant_prompt_unavailable", "O prompt do assistente não está disponível.") from None
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
            raise AssistantFailure(502, "assistant_invalid_response", "O assistente retornou uma resposta inválida. Tente novamente.") from None
