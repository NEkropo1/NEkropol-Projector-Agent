from __future__ import annotations

from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.coldstart.dirty_hacks_to_backlog import coldstart_yunet
from app.routers import health, chat
from app.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Coldstart init…")
    coldstart_yunet()  # dirty hack to download model
    logger.info("Profiler backend startup complete!")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="NEkropol Projector", lifespan=lifespan)
    app.include_router(health.router, tags=["system"])
    app.include_router(chat.router, tags=["chat"])
    return app


app = create_app()
