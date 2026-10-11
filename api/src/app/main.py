from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from redis.asyncio import Redis

from app.errors import ErrorEnvelope, install_error_handlers
from app.ingestion.api.shopify import router as shopify_router
from app.platform.database import Database
from app.platform.health import router
from app.settings import Settings, get_settings
from app.workspace.api.auth import router as auth_router
from app.workspace.service.email_otp import NullEmailSender


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.database = (
            Database(settings.database_url.get_secret_value()) if settings.database_url else None
        )
        app.state.redis = (
            Redis.from_url(
                settings.redis_url.get_secret_value(), socket_connect_timeout=2, socket_timeout=2
            )
            if settings.redis_url
            else None
        )
        try:
            yield
        finally:
            if app.state.redis:
                await app.state.redis.aclose()
            if app.state.database:
                await app.state.database.close()

    app = FastAPI(
        title="Rama Commerce Intelligence",
        version="0.1.0",
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url=None,
        lifespan=lifespan,
        responses={
            status: {"model": ErrorEnvelope}
            for status in (400, 401, 403, 404, 409, 412, 422, 429, 500, 503)
        },
    )
    app.state.settings = settings
    app.state.auth_secrets = None
    app.state.email_sender = NullEmailSender()

    @app.middleware("http")
    async def trace_request(request: Request, call_next):
        request.state.trace_id = uuid4().hex
        response = await call_next(request)
        response.headers["X-Trace-ID"] = request.state.trace_id
        if request.url.path.startswith(("/api/v1/auth/", "/api/v1/me")):
            response.headers["Cache-Control"] = "no-store"
        return response

    install_error_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(shopify_router, prefix="/api/v1")
    return app


app = create_app()
