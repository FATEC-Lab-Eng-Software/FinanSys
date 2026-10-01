from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.database import engine
from src.routers.auth import router as auth_router
from src.shared.supabase.client import close_supabase_client

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    close_supabase_client()
    engine.dispose()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)

app.include_router(auth_router)

@app.get("/")
def read_root():
    return {"status": "Backend FastAPI rodando perfeitamente!"}
