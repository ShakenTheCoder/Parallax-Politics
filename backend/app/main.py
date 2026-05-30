"""FastAPI application entry."""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app import __version__
from app.api.v1 import api_router
from app.config import get_settings
from app.redis import close_redis, get_redis
from app.telemetry.logging import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    log.info("startup", version=__version__)
    # Touch Redis early so connection issues surface at boot.
    try:
        await get_redis().ping()
        log.info("redis.ok")
    except Exception as exc:
        log.warning("redis.unavailable", error=str(exc))
    yield
    await close_redis()
    log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Parallax Politics Backend",
        version=__version__,
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok", "version": __version__, "env": settings.app_env}

    app.include_router(api_router)
    return app


app = create_app()
