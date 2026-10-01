

from datetime import datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.models.auth import User

class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record_failed_login(self, email: str) -> None:
        self._session.execute(
            update(User)
            .where(User.email == email)
            .values(login_attempts=User.login_attempts + 1)
        )
        self._session.commit()

    def record_successful_login(
        self,
        *,
        user_id: UUID,
        email: str,
        first_name: str | None,
        last_name: str | None,
    ) -> None:
        statement = insert(User).values(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            login_attempts=0,
            last_access_at=func.now(),
        )
        statement = statement.on_conflict_do_update(
            index_elements=[User.email],
            set_={
                "id": statement.excluded.id,
                "first_name": statement.excluded.first_name,
                "last_name": statement.excluded.last_name,
                "login_attempts": 0,
                "last_access_at": func.now(),
            },
        )
        self._session.execute(statement)
        self._session.commit()

    def sync_auth_user(
        self,
        *,
        user_id: UUID,
        email: str,
        first_name: str | None,
        last_name: str | None,
        created_at: datetime | None,
        last_access_at: datetime | None,
        role: str = "client",
    ) -> None:

        statement = insert(User).values(
            id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            login_attempts=0,
            created_at=created_at or func.now(),
            last_access_at=last_access_at,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[User.email],
            set_={
                "id": statement.excluded.id,
                "first_name": statement.excluded.first_name,
                "last_name": statement.excluded.last_name,
                "role": statement.excluded.role,
            },
        )
        self._session.execute(statement)
