from typing import Any
from uuid import uuid4

import httpx2

from src.core.config import settings
from src.services.assistant_errors import AssistantFailure


class HermesClient:
    def complete(self, messages: list[dict[str, str]]) -> str:
        if not settings.hermes_api_base_url or not settings.hermes_api_server_key:
            raise AssistantFailure(503, "assistant_not_configured", "O assistente ainda não está configurado.")
        try:
            request_messages = [message.copy() for message in messages]
            if request_messages and request_messages[0].get("role") == "system":
                request_messages[0]["content"] += f"\n\nExecução isolada do FinanSys: {uuid4().hex}."
            with httpx2.Client(timeout=60.0, follow_redirects=False) as client:
                response = client.post(
                    f"{settings.hermes_api_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {settings.hermes_api_server_key}"},
                    json={"model": "hermes-agent", "messages": request_messages, "stream": False},
                )
        except httpx2.TimeoutException:
            raise AssistantFailure(504, "assistant_timeout", "O assistente demorou para responder. Tente novamente.") from None
        except httpx2.RequestError:
            raise AssistantFailure(503, "assistant_unavailable", "Não foi possível conectar ao assistente.") from None
        if not 200 <= response.status_code < 300:
            raise AssistantFailure(502, "assistant_upstream_error", "O assistente não conseguiu processar a mensagem.")
        try:
            body: Any = response.json()
            choice = body["choices"][0]
            content = choice["message"]["content"]
            metadata = body.get("hermes", {})
        except (ValueError, KeyError, IndexError, TypeError):
            raise AssistantFailure(502, "assistant_invalid_response", "O assistente retornou uma resposta inválida.") from None
        if (
            choice.get("finish_reason") not in (None, "stop")
            or isinstance(metadata, dict)
            and (metadata.get("completed") is False or metadata.get("failed") is True or metadata.get("partial") is True)
        ):
            raise AssistantFailure(502, "assistant_incomplete_response", "O assistente não concluiu a resposta. Tente novamente.")
        if not isinstance(content, str) or not content.strip():
            raise AssistantFailure(502, "assistant_invalid_response", "O assistente retornou uma resposta inválida.")
        return content.strip()
