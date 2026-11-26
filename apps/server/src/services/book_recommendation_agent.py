from typing import Any

from src.services.assistant_book_tools import build_google_books_search_tool
from src.services.assistant_tools import AssistantToolContext


class BookRecommendationAgent:
    def __init__(self) -> None:
        self._search_tool = build_google_books_search_tool()

    def recommend(self, context: AssistantToolContext, query: str) -> dict[str, Any]:
        result = self._search_tool.execute(context, {"query": query})
        books = result["books"]
        if not books:
            return {
                "message": "Não encontrei livros em português sobre esse tema no Google Books. Tente descrever o assunto com outras palavras.",
                "books": [],
            }
        return {
            "message": "Encontrei estes livros no Google Books que podem ajudar com esse tema:",
            "books": books,
        }
