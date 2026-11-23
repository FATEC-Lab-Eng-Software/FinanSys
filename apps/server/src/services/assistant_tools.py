from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.transaction import Transaction

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AssistantToolContext:
    session: Session
    user_id: str


class AssistantTool(Protocol):
    name: str
    arguments_schema: dict[str, Any]

    def execute(self, context: AssistantToolContext, arguments: dict[str, Any]) -> dict[str, Any]: ...


class FinancialSummaryTool:
    name = "consultar_resumo_financeiro"
    arguments_schema = {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "format": "date"},
            "end_date": {"type": "string", "format": "date"},
        },
        "required": ["start_date", "end_date"],
        "additionalProperties": False,
    }
    _max_period_days = 366

    def execute(self, context: AssistantToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
        start_date, end_date = _validated_period(arguments, self._max_period_days)
        user_id = UUID(context.user_id)
        criteria = (
            Transaction.user_id == user_id,
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
        )
        amount = Transaction.value
        grouped = context.session.execute(
            select(
                Transaction.type,
                Transaction.category,
                func.sum(amount),
                func.count(Transaction.id),
            )
            .where(*criteria)
            .group_by(Transaction.type, Transaction.category)
        ).all()
        income = sum((Decimal(total) for kind, _, total, _ in grouped if kind == "inflow"), Decimal("0"))
        expense = sum((Decimal(total) for kind, _, total, _ in grouped if kind == "outflow"), Decimal("0"))
        categories = sorted(
            ((category, Decimal(total)) for kind, category, total, _ in grouped if kind == "outflow"),
            key=lambda item: (-item[1], item[0]),
        )
        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "currency": "BRL",
            "income_total": _money(income),
            "expense_total": _money(expense),
            "balance": _money(income - expense),
            "transaction_count": sum(int(count) for _, _, _, count in grouped),
            "expenses_by_category": [
                {"category": category, "total": _money(total)}
                for category, total in categories
            ],
        }


class ToolDecorator:
    def __init__(self, wrapped: AssistantTool) -> None:
        self._wrapped = wrapped

    @property
    def name(self) -> str:
        return self._wrapped.name

    @property
    def arguments_schema(self) -> dict[str, Any]:
        return self._wrapped.arguments_schema

    def execute(self, context: AssistantToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
        return self._wrapped.execute(context, arguments)


class AuthenticatedUserScopeDecorator(ToolDecorator):
    def execute(self, context: AssistantToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(context, AssistantToolContext) or not isinstance(context.session, Session):
            raise ValueError("Contexto de ferramenta inválido")
        if not isinstance(context.user_id, str) or not context.user_id.strip():
            raise ValueError("Usuário autenticado obrigatório")
        try:
            UUID(context.user_id)
        except (ValueError, AttributeError):
            raise ValueError("Identificador de usuário inválido") from None
        return super().execute(context, arguments)


class AuditToolDecorator(ToolDecorator):
    def execute(self, context: AssistantToolContext, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            result = super().execute(context, arguments)
        except Exception:
            logger.warning("assistant_tool name=%s success=false", self.name)
            raise
        logger.info("assistant_tool name=%s success=true", self.name)
        return result


def build_financial_summary_tool() -> AssistantTool:
    return AuditToolDecorator(AuthenticatedUserScopeDecorator(FinancialSummaryTool()))


def _validated_period(arguments: dict[str, Any], max_days: int) -> tuple[date, date]:
    if not isinstance(arguments, dict) or set(arguments) != {"start_date", "end_date"}:
        raise ValueError("Informe somente start_date e end_date")
    parsed: list[date] = []
    for key in ("start_date", "end_date"):
        value = arguments[key]
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError(f"{key} deve ser uma data ISO (YYYY-MM-DD)")
        try:
            parsed.append(date.fromisoformat(value))
        except ValueError:
            raise ValueError(f"{key} deve ser uma data ISO válida") from None
    start_date, end_date = parsed
    if start_date > end_date:
        raise ValueError("A data inicial deve ser anterior ou igual à data final")
    if (end_date - start_date).days + 1 > max_days:
        raise ValueError(f"O período não pode exceder {max_days} dias")
    return start_date, end_date


def _money(value: Decimal) -> str:
    return f"{value:.2f}"
