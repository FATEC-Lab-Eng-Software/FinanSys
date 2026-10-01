

from uuid import UUID

from sqlalchemy.orm import Session

from src.repositories.auth import UserRepository
from src.schemas.auth import AuthenticatedUser
from src.services.auth.errors import AuthFailure

class UserAccessService:
    def __init__(self, session: Session) -> None:
        self._users = UserRepository(session)

    def record_failed_login(self, email: str) -> None:
        try:
            self._users.record_failed_login(email)
        except Exception:
            raise AuthFailure(
                503,
                "user_store_unavailable",
                "Não foi possível concluir a autenticação.",
                "user_store_unavailable",
            ) from None

    def record_successful_login(self, user: AuthenticatedUser) -> None:
        if not user.email:
            raise AuthFailure(
                502,
                "authentication_failed",
                "Não foi possível concluir a autenticação.",
                "provider_failure",
            )
        try:
            self._users.record_successful_login(
                user_id=UUID(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
            )
        except Exception:
            raise AuthFailure(
                503,
                "user_store_unavailable",
                "Não foi possível concluir a autenticação.",
                "user_store_unavailable",
            ) from None
