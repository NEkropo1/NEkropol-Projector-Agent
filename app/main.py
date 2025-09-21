
from __future__ import annotations

from fastapi import FastAPI
from app.routers import health, chat


def create_app() -> FastAPI:
    app = FastAPI(title="NEkropol Projector")
    app.include_router(health.router, tags=["system"])
    app.include_router(chat.router, tags=["chat"])
    return app


app = create_app()
