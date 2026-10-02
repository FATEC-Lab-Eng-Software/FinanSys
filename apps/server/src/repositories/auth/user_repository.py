

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from src.models.auth import User

class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record_failed_login(self, email: str) -> None:
        self.record_failed_login_and_get_lockout(email)

    def check_login_lockout(self, email: str) -> datetime | None:
        normalized_email = email.strip().lower()
        self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:email, 0))"),
            {"email": normalized_email},
        )
        self._session.execute(
            text(
                "UPDATE users SET login_attempts = 0, lockout_until = NULL "
                "WHERE email = :email AND lockout_until IS NOT NULL AND lockout_until <= clock_timestamp()"
            ),
            {"email": normalized_email},
        )
        result = self._session.execute(
            text("SELECT lockout_until FROM users WHERE email = :email"),
            {"email": normalized_email},
        ).first()
        if result is None or result[0] is None:
            return None
        locked_until = result[0]
        if locked_until is not None:
            self._session.rollback()
            return locked_until
        return None

    def record_failed_login_and_get_lockout(self, email: str) -> datetime | None:
        result = self._session.execute(
            text(
                "UPDATE users SET login_attempts = login_attempts + 1, "
                "lockout_until = CASE WHEN login_attempts + 1 >= 5 "
                "THEN clock_timestamp() + interval '10 minutes' ELSE NULL END "
                "WHERE email = :email RETURNING login_attempts, lockout_until"
            ),
            {"email": email.strip().lower()},
        ).first()
        self._session.commit()
        if result is None or result[0] < 5:
            return None
        return result[1]

    def check_session_activity(self, user_id: UUID, now: datetime) -> bool:
        result = self._session.execute(
            update(User)
            .where(
                User.id == user_id,
                User.last_activity_at.is_not(None),
                User.last_activity_at > now - timedelta(minutes=15),
            )
            .values(last_activity_at=now, last_access_at=now)
            .returning(User.id)
        ).first()
        self._session.commit()
        return result is not None

    def is_session_active(self, user_id: UUID, now: datetime) -> bool:
        return bool(
            self._session.scalar(
                select(User.id).where(
                    User.id == user_id,
                    User.last_activity_at.is_not(None),
                    User.last_activity_at > now - timedelta(minutes=15),
                )
            )
        )

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
            last_activity_at=func.now(),
            lockout_until=None,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[User.email],
            set_={
                "id": statement.excluded.id,
                "first_name": statement.excluded.first_name,
                "last_name": statement.excluded.last_name,
                "login_attempts": 0,
                "last_access_at": func.now(),
                "last_activity_at": func.now(),
                "lockout_until": None,
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
