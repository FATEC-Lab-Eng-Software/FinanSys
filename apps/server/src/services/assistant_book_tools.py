from __future__ import annotations

from typing import Any

from src.services.assistant_tools import (
    AssistantTool,
    AssistantToolContext,
    AuditToolDecorator,
    AuthenticatedUserScopeDecorator,
    ToolDecorator,
)
from src.services.google_books_client import GoogleBooksClient


class GoogleBooksSearchTool:
    name = "buscar_livros_google_books"
    arguments_schema = {
        "type": "object",
        "properties": {"query": {"type": "string", "minLength": 1, "maxLength": 180}},
        "required": ["query"],
        "additionalProperties": False,
    }

    def execute(self, context: AssistantToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(arguments, dict) or set(arguments) != {"query"}:
            raise ValueError("Argumentos inválidos para busca de livros.")
        query = arguments["query"]
        if not isinstance(query, str) or not query.strip() or len(query) > 180:
            raise ValueError("Informe um tema válido para buscar livros.")
        return {"books": GoogleBooksClient().search(query)}


def build_google_books_search_tool() -> AssistantTool:
    return AuditToolDecorator(AuthenticatedUserScopeDecorator(ToolDecorator(GoogleBooksSearchTool())))
