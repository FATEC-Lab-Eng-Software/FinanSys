from __future__ import annotations

import sys
from datetime import datetime
from uuid import UUID

import httpx2
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import settings
from src.core.database import SessionLocal, engine
from src.repositories.auth import UserRepository

PAGE_SIZE = 1000
SEEDED_PASSWORD = "123456789"
SEEDED_PROFILES = (
    {
        "role": "admin",
        "email": "admin@finansys.com",
        "first_name": "Admin",
        "last_name": "FinanSys",
    },
    {
        "role": "client",
        "email": "pedro@gmail.com",
        "first_name": "Pedro",
        "last_name": "Cliente",
    },
    {
        "role": "client",
        "email": "maria@gmail.com",
        "first_name": "Maria",
        "last_name": "Cliente",
    },
)


def _timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _profile(metadata: object) -> tuple[str | None, str | None]:
    if not isinstance(metadata, dict):
        return None, None
    first = metadata.get("first_name") or metadata.get("given_name")
    last = metadata.get("last_name") or metadata.get("family_name")
    full = metadata.get("full_name") or metadata.get("name")
    if isinstance(full, str):
        parts = full.strip().split(maxsplit=1)
        if parts:
            first = first or parts[0]
        if len(parts) > 1:
            last = last or parts[1]
    return (
        first if isinstance(first, str) else None,
        last if isinstance(last, str) else None,
    )


def _headers() -> dict[str, str]:
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError(
            "Configure SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY para executar o seed."
        )
    return {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
    }


def _auth_users(
    client: httpx2.Client, headers: dict[str, str]
) -> list[dict[str, object]]:
    users: list[dict[str, object]] = []
    page = 1
    while True:
        response = client.get(
            f"{settings.supabase_url}/auth/v1/admin/users",
            params={"page": page, "per_page": PAGE_SIZE},
            headers=headers,
        )
        response.raise_for_status()
        payload = response.json()
        page_users = payload.get("users") if isinstance(payload, dict) else None
        if not isinstance(page_users, list):
            raise RuntimeError(
                "Resposta inválida ao consultar usuários do Supabase Auth."
            )
        users.extend(user for user in page_users if isinstance(user, dict))
        if len(page_users) < PAGE_SIZE:
            return users
        page += 1


def _ensure_seed_accounts(
    client: httpx2.Client,
    headers: dict[str, str],
    users: list[dict[str, object]],
    profiles: list[dict[str, str]],
) -> None:
    by_email = {
        email.lower(): user
        for user in users
        if isinstance((email := user.get("email")), str) and email
    }
    for profile in profiles:
        email = profile["email"]
        user = by_email.get(email)
        if user is None:
            response = client.post(
                f"{settings.supabase_url}/auth/v1/invite",
                headers=headers,
                json={
                    "email": email,
                    "data": {
                        "first_name": profile["first_name"],
                        "last_name": profile["last_name"],
                    },
                },
            )
            response.raise_for_status()
            user = response.json()
            if not isinstance(user, dict) or not isinstance(user.get("id"), str):
                raise RuntimeError(
                    "Resposta inválida ao convidar usuário no Supabase Auth."
                )
            by_email[email] = user

        user_id = user.get("id")
        if not isinstance(user_id, str):
            raise RuntimeError("Usuário do Supabase Auth sem identificador válido.")
        app_metadata = user.get("app_metadata")
        updated_app_metadata = (
            dict(app_metadata) if isinstance(app_metadata, dict) else {}
        )
        updated_app_metadata["role"] = profile["role"]
        user_metadata = user.get("user_metadata")
        updated_user_metadata = (
            dict(user_metadata) if isinstance(user_metadata, dict) else {}
        )
        updated_user_metadata.update(
            {"first_name": profile["first_name"], "last_name": profile["last_name"]}
        )
        response = client.put(
            f"{settings.supabase_url}/auth/v1/admin/users/{user_id}",
            headers=headers,
            json={
                "password": SEEDED_PASSWORD,
                "email_confirm": True,
                "app_metadata": updated_app_metadata,
                "user_metadata": updated_user_metadata,
            },
        )
        response.raise_for_status()
        updated_user = response.json()
        if isinstance(updated_user, dict):
            by_email[email] = updated_user


def seed() -> int:
    headers = _headers()
    profiles = list(SEEDED_PROFILES)
    with httpx2.Client(timeout=30.0) as client:
        users = _auth_users(client, headers)
        _ensure_seed_accounts(client, headers, users, profiles)
        users = _auth_users(client, headers)

    role_by_email = {profile["email"]: profile["role"] for profile in profiles}
    synced = 0
    with SessionLocal.begin() as session:
        repository = UserRepository(session)
        for auth_user in users:
            user_id = auth_user.get("id")
            email = auth_user.get("email")
            if not isinstance(user_id, str) or not isinstance(email, str) or not email:
                continue
            try:
                parsed_id = UUID(user_id)
            except ValueError:
                continue
            normalized_email = email.lower()
            first_name, last_name = _profile(auth_user.get("user_metadata"))
            app_metadata = auth_user.get("app_metadata")
            role = role_by_email.get(normalized_email)
            if (
                role is None
                and isinstance(app_metadata, dict)
                and app_metadata.get("role") in {"admin", "client"}
            ):
                role = app_metadata["role"]
            repository.sync_auth_user(
                user_id=parsed_id,
                email=normalized_email,
                first_name=first_name,
                last_name=last_name,
                created_at=_timestamp(auth_user.get("created_at")),
                last_access_at=_timestamp(auth_user.get("last_sign_in_at")),
                role=role or "client",
            )
            synced += 1
    return synced


def run() -> None:
    try:
        synced = seed()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from None
    except httpx2.ConnectError:
        print(
            f"Não foi possível conectar ao Supabase em {settings.supabase_url}. Verifique `docker compose ps`.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    except httpx2.TimeoutException:
        print("Tempo esgotado ao conectar ao Supabase.", file=sys.stderr)
        raise SystemExit(1) from None
    except httpx2.HTTPStatusError as error:
        provider_code = ""
        try:
            payload = error.response.json()
            if isinstance(payload, dict):
                candidate = payload.get("code") or payload.get("error_code")
                if isinstance(candidate, str) and candidate.replace("_", "").isalnum():
                    provider_code = candidate
        except (ValueError, TypeError):
            pass
        suffix = f" ({provider_code})" if provider_code else ""
        print(
            f"Supabase respondeu HTTP {error.response.status_code}{suffix}.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    except httpx2.HTTPError as error:
        print(
            f"Falha na comunicação com Supabase ({type(error).__name__}).",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    except SQLAlchemyError as error:
        original_error = getattr(error, "orig", None)
        detail = (
            str(original_error).splitlines()[0][:240]
            if original_error
            else type(error).__name__
        )
        print(f"Falha ao sincronizar o banco de dados: {detail}", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        engine.dispose()
    print(f"Seed concluído. Perfis sincronizados: {synced}.")


if __name__ == "__main__":
    run()


