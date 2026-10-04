from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.models.transaction import Transaction
from src.repositories.transactions_repository import TransactionRepository
from src.schemas.transactions_schemas import (
    TransactionCreate,
    TransactionFilters,
    TransactionResponse,
    TransactionUpdate,
)

class TransactionFailure(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message

class TransactionService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._transactions = TransactionRepository(session)

    def create(self, user_id: str, payload: TransactionCreate) -> TransactionResponse:
        try:
            transaction = self._transactions.create(
                user_id=UUID(user_id),
                values=payload.model_dump(),
            )
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return TransactionResponse.model_validate(transaction)

    def list_for_user(self, user_id: str, filters: TransactionFilters) -> list[TransactionResponse]:
        try:
            transactions = self._transactions.list_for_user(user_id=UUID(user_id), filters=filters)
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return [TransactionResponse.model_validate(transaction) for transaction in transactions]

    def get(self, user_id: str, transaction_id: int) -> TransactionResponse:
        return TransactionResponse.model_validate(self._find(user_id, transaction_id))

    def update(self, user_id: str, transaction_id: int, payload: TransactionUpdate) -> TransactionResponse:
        transaction = self._find(user_id, transaction_id)
        try:
            transaction = self._transactions.update(
                transaction,
                values=payload.model_dump(exclude_unset=True),
            )
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return TransactionResponse.model_validate(transaction)

    def delete(self, user_id: str, transaction_id: int) -> None:
        transaction = self._find(user_id, transaction_id)
        try:
            self._transactions.delete(transaction)
        except SQLAlchemyError:
            raise self._store_unavailable() from None

    def _find(self, user_id: str, transaction_id: int) -> Transaction:
        try:
            transaction = self._transactions.get_for_user(
                transaction_id=transaction_id,
                user_id=UUID(user_id),
            )
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        if transaction is None:
            raise TransactionFailure(404, "transaction_not_found", "Transação não encontrada.")
        return transaction

    def _store_unavailable(self) -> TransactionFailure:
        self._session.rollback()
        return TransactionFailure(
            503,
            "transaction_store_unavailable",
            "Não foi possível acessar as transações.",
        )