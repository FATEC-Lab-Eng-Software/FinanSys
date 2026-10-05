from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.transaction import Transaction
from src.schemas.transactions_schemas import TransactionFilters

class TransactionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, user_id: UUID, values: dict[str, object]) -> Transaction:
        transaction = Transaction(user_id=user_id, **values)
        self._session.add(transaction)
        self._session.commit()
        self._session.refresh(transaction)
        return transaction

    def get_for_user(self, *, transaction_id: int, user_id: UUID) -> Transaction | None:
        return self._session.scalar(
            select(Transaction).where(
                Transaction.id == transaction_id,
                Transaction.user_id == user_id,
            )
        )

    def list_for_user(self, *, user_id: UUID, filters: TransactionFilters) -> list[Transaction]:
        statement = select(Transaction).where(Transaction.user_id == user_id)
        if filters.start_date is not None:
            statement = statement.where(Transaction.transaction_date >= filters.start_date)
        if filters.end_date is not None:
            statement = statement.where(Transaction.transaction_date <= filters.end_date)
        if filters.type is not None:
            statement = statement.where(Transaction.type == filters.type)
        if filters.category is not None:
            statement = statement.where(Transaction.category == filters.category)
        statement = (
            statement.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
            .limit(filters.limit)
            .offset(filters.offset)
        )
        return list(self._session.scalars(statement))

    def update(self, transaction: Transaction, *, values: dict[str, object]) -> Transaction:
        for field, value in values.items():
            setattr(transaction, field, value)
        self._session.commit()
        self._session.refresh(transaction)
        return transaction

    def delete(self, transaction: Transaction) -> None:
        self._session.delete(transaction)
        self._session.commit()