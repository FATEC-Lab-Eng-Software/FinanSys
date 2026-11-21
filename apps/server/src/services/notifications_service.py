from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.repositories.notifications_repository import NotificationRepository
from src.schemas.notification import NotificationResponse


class NotificationFailure(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class NotificationService:
    def __init__(self, session: Session) -> None:
        self._session = session
        self._notifications = NotificationRepository(session)

    def create(self, user_id: str, *, category: str, title: str, description: str) -> None:
        try:
            self._notifications.create(
                user_id=UUID(user_id), category=category, title=title, description=description
            )
        except SQLAlchemyError:
            self._session.rollback()

    def list_for_user(self, user_id: str) -> list[NotificationResponse]:
        try:
            items = self._notifications.list_for_user(UUID(user_id))
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        return [NotificationResponse.model_validate(item) for item in items]

    def delete(self, user_id: str, notification_id: int) -> None:
        try:
            deleted = self._notifications.delete_for_user(notification_id, UUID(user_id))
        except SQLAlchemyError:
            raise self._store_unavailable() from None
        if not deleted:
            raise NotificationFailure(404, "notification_not_found", "Notificação não encontrada.")

    def delete_all(self, user_id: str) -> None:
        try:
            self._notifications.delete_all_for_user(UUID(user_id))
        except SQLAlchemyError:
            raise self._store_unavailable() from None

    def _store_unavailable(self) -> NotificationFailure:
        self._session.rollback()
        return NotificationFailure(
            503,
            "notification_store_unavailable",
            "Não foi possível acessar as notificações.",
        )
