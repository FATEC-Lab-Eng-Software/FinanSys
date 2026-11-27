from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import quote

import httpx2

from src.core.config import settings
from src.services.assistant_errors import AssistantFailure


class GoogleBooksClient:
    _endpoint = "https://www.googleapis.com/books/v1/volumes"

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        normalized_query = " ".join(query.split())[:180]
        if not normalized_query:
            raise ValueError("Informe o tema para buscar livros.")
        if not settings.google_books_api_key:
            raise AssistantFailure(503, "books_not_configured", "A busca de livros ainda não está configurada.")

        try:
            with httpx2.Client(timeout=12.0, follow_redirects=False) as client:
                response = client.get(
                    self._endpoint,
                    params={
                        "q": normalized_query,
                        "maxResults": min(max(limit, 1), 10),
                        "printType": "books",
                        "langRestrict": "pt",
                        "orderBy": "relevance",
                        "key": settings.google_books_api_key,
                    },
                    headers={"Accept": "application/json"},
                )
        except httpx2.TimeoutException:
            raise AssistantFailure(504, "books_search_timeout", "A busca de livros demorou para responder.") from None
        except httpx2.RequestError:
            raise AssistantFailure(503, "books_search_unavailable", "Não foi possível conectar ao Google Books.") from None

        if not 200 <= response.status_code < 300:
            raise AssistantFailure(503, "books_search_unavailable", "O Google Books não conseguiu concluir a busca.")
        try:
            payload: Any = response.json()
        except ValueError:
            raise AssistantFailure(502, "books_search_invalid_response", "O Google Books retornou uma resposta inválida.") from None
        if not isinstance(payload, dict):
            raise AssistantFailure(502, "books_search_invalid_response", "O Google Books retornou uma resposta inválida.")

        items = payload.get("items", [])
        if not isinstance(items, list):
            raise AssistantFailure(502, "books_search_invalid_response", "O Google Books retornou uma resposta inválida.")
        return [book for item in items if (book := self._normalize_book(item)) is not None]

    @staticmethod
    def _normalize_book(item: Any) -> dict[str, Any] | None:
        if not isinstance(item, dict) or not isinstance(item.get("volumeInfo"), dict):
            return None
        volume_id = item.get("id")
        volume = item["volumeInfo"]
        title = volume.get("title")
        if not isinstance(volume_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", volume_id):
            return None
        if not isinstance(title, str) or not title.strip():
            return None
        authors = volume.get("authors", [])
        authors = [author.strip()[:120] for author in authors if isinstance(author, str) and author.strip()] if isinstance(authors, list) else []
        description = volume.get("description")
        description = re.sub(r"<[^>]*>", " ", description) if isinstance(description, str) else ""
        description = " ".join(html.unescape(description).split())[:700]
        published_date = volume.get("publishedDate")
        return {
            "title": title.strip()[:240],
            "authors": authors[:5],
            "description": description,
            "published_date": published_date[:32] if isinstance(published_date, str) else None,
            "info_link": f"https://books.google.com/books?id={quote(volume_id, safe='')}",
        }
