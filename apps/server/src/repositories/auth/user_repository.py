

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.models.auth import User

class UserRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record_failed_login(self, email: str) -> None:
        self.record_failed_login_and_get_lockout(email)

    def is_account_active(self, email: str) -> bool:
        user = self._session.scalar(select(User).where(User.email == email.strip().lower()))
        return user is None or user.is_active

    def access_profile(self, user_id: UUID) -> tuple[str, bool] | None:
        user = self._session.scalar(select(User).where(User.id == user_id))
        if user is None:
            return None
        return user.role, user.is_active

    def list_clients(self, *, search: str, active: bool | None, limit: int, offset: int) -> list[User]:
        statement = select(User).where(User.role == "client")
        if search:
            pattern = f"%{search.strip()}%"
            statement = statement.where(or_(User.email.ilike(pattern), User.first_name.ilike(pattern), User.last_name.ilike(pattern)))
        if active is not None:
            statement = statement.where(User.is_active == active)
        return list(self._session.scalars(statement.order_by(User.created_at.desc()).limit(limit).offset(offset)))

    def client_overview(self) -> dict[str, int]:
        month_start = func.date_trunc("month", func.current_timestamp())
        values = self._session.execute(
            select(
                func.count(User.id),
                func.count(User.id).filter(User.is_active.is_(True)),
                func.count(User.id).filter(User.is_active.is_(False)),
                func.count(User.id).filter(User.created_at >= month_start),
            ).where(User.role == "client")
        ).one()
        return {
            "clients_total": values[0],
            "clients_active": values[1],
            "clients_suspended": values[2],
            "clients_created_this_month": values[3],
        }

    def update_client_status(self, user_id: UUID, active: bool) -> User | None:
        user = self._session.scalar(select(User).where(User.id == user_id, User.role == "client"))
        if user is None:
            return None
        user.is_active = active
        self._session.commit()
        self._session.refresh(user)
        return user

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
                "INSERT INTO users (id, email, role, login_attempts, created_at) "
                "VALUES (:id, :email, 'client', 1, clock_timestamp()) "
                "ON CONFLICT (email) DO UPDATE SET "
                "login_attempts = users.login_attempts + 1, "
                "lockout_until = CASE WHEN users.login_attempts + 1 >= 5 "
                "THEN clock_timestamp() + interval '10 minutes' ELSE NULL END "
                "RETURNING login_attempts, lockout_until"
            ),
            {"id": uuid4(), "email": email.strip().lower()},
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
                User.is_active.is_(True),
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
                    User.is_active.is_(True),
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
