from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, *, user_id: UUID, category: str, title: str, description: str) -> None:
        notification = Notification(
            user_id=user_id,
            category=category,
            title=title,
            description=description,
        )
        self._session.add(notification)

    def list_for_user(self, user_id: UUID) -> list[Notification]:
        statement = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
        )
        return list(self._session.scalars(statement))

    def delete_for_user(self, notification_id: int, user_id: UUID) -> bool:
        notification = self._session.scalar(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        if notification is None:
            return False
        self._session.delete(notification)
        self._session.commit()
        return True

    def delete_all_for_user(self, user_id: UUID) -> None:
        self._session.execute(delete(Notification).where(Notification.user_id == user_id))
        self._session.commit()
