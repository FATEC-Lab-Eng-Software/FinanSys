from typing import Any

import httpx2

from src.core.config import settings
from src.schemas.assistant import AssistantMessage

SYSTEM_MESSAGE = (
    "Você é o assistente do FinanSys. Converse em português brasileiro, com clareza e objetividade. "
    "Nesta versão você não tem acesso a ferramentas, dados financeiros, arquivos ou email. "
    "Não afirme que consultou dados, criou relatórios ou realizou ações. "
    "Quando pedirem algo que dependa desses recursos, explique essa limitação com brevidade."
)


class AssistantFailure(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AssistantService:
    def chat(self, messages: list[AssistantMessage]) -> str:
        if not settings.hermes_api_base_url or not settings.hermes_api_server_key:
            raise AssistantFailure(
                503,
                "assistant_not_configured",
                "O assistente ainda não está configurado.",
            )

        request_messages = [{"role": "system", "content": SYSTEM_MESSAGE}]
        request_messages.extend(message.model_dump() for message in messages)

        try:
            with httpx2.Client(timeout=60.0, follow_redirects=False) as client:
                response = client.post(
                    f"{settings.hermes_api_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.hermes_api_server_key}"},
                    json={
                        "model": "hermes-agent",
                        "messages": request_messages,
                        "stream": False,
                    },
                )
        except httpx2.TimeoutException:
            raise AssistantFailure(
                504,
                "assistant_timeout",
                "O assistente demorou para responder. Tente novamente.",
            ) from None
        except httpx2.RequestError:
            raise AssistantFailure(
                503,
                "assistant_unavailable",
                "Não foi possível conectar ao assistente.",
            ) from None

        if not 200 <= response.status_code < 300:
            raise AssistantFailure(
                502,
                "assistant_upstream_error",
                "O assistente não conseguiu processar a mensagem.",
            )

        try:
            body: Any = response.json()
            message = body["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            raise AssistantFailure(
                502,
                "assistant_invalid_response",
                "O assistente retornou uma resposta inválida.",
            ) from None

        if not isinstance(message, str) or not message.strip():
            raise AssistantFailure(
                502,
                "assistant_invalid_response",
                "O assistente retornou uma resposta inválida.",
            )
        return message.strip()
