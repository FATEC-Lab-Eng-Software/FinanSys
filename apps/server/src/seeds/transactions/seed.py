from __future__ import annotations

import sys
from calendar import monthrange
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.core.database import SessionLocal, engine
from src.models.auth import Transaction, User

DEMO_EMAILS = ("pedro@gmail.com", "maria@gmail.com")
MONTHLY_EXPENSES = (
    ("520.00", "215.00", "170.00", "0.00", "0.00"),
    ("555.00", "230.00", "180.00", "85.00", "0.00"),
    ("535.00", "225.00", "190.00", "0.00", "0.00"),
    ("590.00", "245.00", "185.00", "0.00", "360.00"),
    ("610.00", "250.00", "205.00", "120.00", "0.00"),
    ("640.00", "265.00", "220.00", "0.00", "0.00"),
)


def _month_date(today: date, months_ago: int, day: int) -> date:
    month_index = today.year * 12 + today.month - 1 - months_ago
    year, month = divmod(month_index, 12)
    month += 1
    day = min(day, monthrange(year, month)[1])
    if year == today.year and month == today.month:
        day = min(day, today.day)
    return date(year, month, day)


def _sample_transactions(today: date) -> list[dict[str, object]]:
    transactions: list[dict[str, object]] = []
    for index, months_ago in enumerate(range(5, -1, -1)):
        food, utilities, transportation, medical, travel = MONTHLY_EXPENSES[index]
        transactions.extend(
            [
                {
                    "type": "inflow",
                    "category": "work",
                    "transaction_date": _month_date(today, months_ago, 1),
                    "value": Decimal("4200.00"),
                    "source_money": "Salário",
                },
                {
                    "type": "outflow",
                    "category": "housing",
                    "transaction_date": _month_date(today, months_ago, 5),
                    "value": Decimal("1250.00"),
                    "source_money": "Conta corrente",
                },
                {
                    "type": "outflow",
                    "category": "food",
                    "transaction_date": _month_date(today, months_ago, 10),
                    "value": Decimal(food),
                    "source_money": "Cartão de crédito",
                },
                {
                    "type": "outflow",
                    "category": "utilities",
                    "transaction_date": _month_date(today, months_ago, 15),
                    "value": Decimal(utilities),
                    "source_money": "Conta corrente",
                },
                {
                    "type": "outflow",
                    "category": "transportation",
                    "transaction_date": _month_date(today, months_ago, 20),
                    "value": Decimal(transportation),
                    "source_money": "Cartão de crédito",
                },
            ]
        )
        if medical != "0.00":
            transactions.append(
                {
                    "type": "outflow",
                    "category": "medical",
                    "transaction_date": _month_date(today, months_ago, 22),
                    "value": Decimal(medical),
                    "source_money": "Cartão de crédito",
                }
            )
        if travel != "0.00":
            transactions.append(
                {
                    "type": "outflow",
                    "category": "travel",
                    "transaction_date": _month_date(today, months_ago, 24),
                    "value": Decimal(travel),
                    "source_money": "Cartão de crédito",
                }
            )
        if index == 2:
            transactions.append(
                {
                    "type": "inflow",
                    "category": "work",
                    "transaction_date": _month_date(today, months_ago, 25),
                    "value": Decimal("650.00"),
                    "source_money": "Trabalho extra",
                }
            )
    return transactions


def _seed_user(session: Session, user_id: UUID, today: date) -> int:
    existing_id = session.scalar(
        select(Transaction.id).where(Transaction.user_id == user_id).limit(1)
    )
    if existing_id is not None:
        return 0
    transactions = [
        Transaction(user_id=user_id, **values) for values in _sample_transactions(today)
    ]
    session.add_all(transactions)
    return len(transactions)


def seed() -> int:
    created = 0
    today = date.today()
    with SessionLocal.begin() as session:
        for email in DEMO_EMAILS:
            user = session.scalar(select(User).where(User.email == email))
            if user is not None:
                created += _seed_user(session, user.id, today)
    return created


def run() -> None:
    try:
        created = seed()
    except SQLAlchemyError as error:
        original_error = getattr(error, "orig", None)
        detail = (
            str(original_error).splitlines()[0][:240]
            if original_error
            else type(error).__name__
        )
        print(f"Falha ao criar transações de demonstração: {detail}", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        engine.dispose()
    print(f"Transações de demonstração criadas: {created}.")
