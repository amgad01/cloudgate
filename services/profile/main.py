from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from services.profile.api.routes import router
from shared.config import get_profile_config
from shared.database.connection import init_database
from shared.database.redis import init_redis
from shared.middleware.logging import LoggingMiddleware, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    config = get_profile_config()

    if config.app_env == "production":
        if (
            "change-me" in config.secret_key.lower()
            or "change-me" in config.jwt_secret_key.lower()
        ):
            raise ValueError(
                "Default secrets detected in production environment. "
                "Please set SECRET_KEY and JWT_SECRET_KEY environment variables."
            )

    setup_logging(config)
    db = init_database(config)
    redis = init_redis(config)

    yield

    await db.close()
    await redis.close()


def create_app() -> FastAPI:
    config = get_profile_config()

    app = FastAPI(
        title="CloudGate Profile Service",
        description="Manage user profiles and preferences",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(LoggingMiddleware, service_name="profile")

    app.mount("/metrics", make_asgi_app())

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": "profile", "status": "ok"}

    @app.get("/api/v1/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    return app


app = create_app()
