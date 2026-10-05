

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

SERVER_DIRECTORY = Path(__file__).resolve().parents[2]
PROJECT_DIRECTORY = SERVER_DIRECTORY.parents[1]
load_dotenv(SERVER_DIRECTORY / ".env")
load_dotenv(PROJECT_DIRECTORY / ".env")

class Settings:

    def __init__(self) -> None:
        self.database_url = self._database_url()
        self.database_echo = os.getenv("DATABASE_ECHO", "false").lower() in {
            "1",
            "true",
            "yes",
        }
        self.database_pool_size = int(os.getenv("DATABASE_POOL_SIZE", "5"))
        self.database_max_overflow = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
        self.supabase_url = (os.getenv("SUPABASE_URL") or "http://localhost:8080").strip().rstrip("/")
        self.supabase_public_key = (
            os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("ANON_KEY")
            or ""
        ).strip()
        self.supabase_service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        self.cors_allowed_origins = self._origin_list(
            "CORS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        )
        self.auth_trusted_origins = self._origin_list("AUTH_TRUSTED_ORIGINS", "")
        self.auth_password_recovery_redirect = (
            os.getenv("AUTH_PASSWORD_RECOVERY_REDIRECT")
            or "http://localhost:3000/password-recovery"
        ).strip()
        self.auth_cookie_secure = os.getenv("AUTH_COOKIE_SECURE", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        self.auth_cookie_samesite = os.getenv("AUTH_COOKIE_SAMESITE", "lax").strip().lower()

    @staticmethod
    def _origin_list(name: str, default: str) -> tuple[str, ...]:
        return tuple(value.strip() for value in os.getenv(name, default).split(",") if value.strip())

    @staticmethod
    def _database_url() -> str:
        configured_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL")
        if configured_url:

            if configured_url.startswith("postgres://"):
                return configured_url.replace("postgres://", "postgresql+psycopg://", 1)
            if configured_url.startswith("postgresql://"):
                return configured_url.replace("postgresql://", "postgresql+psycopg://", 1)
            return configured_url

        user = quote_plus(os.getenv("POSTGRES_USER", "postgres"))
        password = quote_plus(os.getenv("POSTGRES_PASSWORD", "postgres"))
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = quote_plus(os.getenv("POSTGRES_DB", "postgres"))
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"

@lru_cache(maxsize=1)
def get_settings() -> Settings:

    return Settings()

settings = get_settings()
