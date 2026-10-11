import hmac
from typing import Annotated
from uuid import UUID

from app.errors import AppError
from app.workspace.service.auth import AuthService, LoginLimiter
from app.workspace.service.auth_secrets import load_auth_secrets
from app.workspace.service.rbac import permitted
from app.workspace.service.session import authenticated_user, csrf_token
from fastapi import Depends, Header, Request
from sqlalchemy import text

COOKIE_NAME = "rci_session"


def database(request: Request):
    if request.app.state.database is None:
        raise AppError(503, "DATABASE_UNAVAILABLE", "Database is not configured.")
    return request.app.state.database


def auth_service(request: Request, *, require_secrets: bool = False) -> AuthService:
    settings = request.app.state.settings
    password_only = settings.env == "local" and settings.local_password_login
    secret_store = request.app.state.auth_secrets
    if secret_store is None and (not password_only or require_secrets):
        secret_store = load_auth_secrets(request.app.state.settings)
    return AuthService(
        database(request), secret_store, request.app.state.email_sender, password_only=password_only
    )


def check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    allowed = {request.app.state.settings.web_origin, str(request.base_url).rstrip("/")}
    if origin is not None and origin not in allowed:
        raise AppError(403, "ORIGIN_REJECTED", "Request origin is not allowed.")


async def rate_limit(request: Request, *, email: str | None = None) -> None:
    redis = request.app.state.redis
    if redis is None:
        raise AppError(503, "AUTH_LIMITER_UNAVAILABLE", "Sign in is temporarily unavailable.")
    limiter = LoginLimiter(redis)
    client = request.client.host if request.client else "unknown"
    await limiter.check("ip", client, 60)
    if email:
        await limiter.check("account", email.strip().casefold(), 5)


async def current_user(request: Request):
    settings = request.app.state.settings
    return await authenticated_user(
        database(request),
        request.cookies.get(COOKIE_NAME),
        allow_password_login=settings.env == "local" and settings.local_password_login,
    )


async def csrf_protected(
    request: Request,
    csrf_header: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
    user=Depends(current_user),
):
    check_origin(request)
    token = request.cookies.get(COOKIE_NAME)
    supplied = csrf_header or ""
    if not token or not hmac.compare_digest(csrf_token(token).encode(), supplied.encode()):
        raise AppError(403, "CSRF_REJECTED", "Request verification token is missing or invalid.")
    return user


async def selected_workspace(
    request: Request,
    workspace_id: Annotated[UUID, Header(alias="X-Workspace-Id")],
    user=Depends(current_user),
):
    async with database(request).identity_transaction(user["id"]) as session:
        member = (
            await session.execute(
                text("""
            SELECT EXISTS (SELECT 1 FROM ws.permission_scope
              WHERE user_id=:user AND workspace_id=:workspace
                AND (expires_at IS NULL OR expires_at>now()))
        """),
                {"user": user["id"], "workspace": workspace_id},
            )
        ).scalar_one()
    if not member:
        raise AppError(404, "NOT_FOUND", "Workspace was not found.")
    return workspace_id


def require_permission(function: str, *, product: str, market: str):
    async def dependency(
        request: Request, workspace=Depends(selected_workspace), user=Depends(current_user)
    ):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            await csrf_protected(
                request, csrf_header=request.headers.get("x-csrf-token"), user=user
            )
        async with database(request).transaction(workspace) as session:
            if not await permitted(session, user["id"], workspace, function, product, market):
                raise AppError(404, "NOT_FOUND", "Resource was not found.")
            if request.method not in {"GET", "HEAD", "OPTIONS"}:
                demo = (
                    await session.execute(
                        text("SELECT demo_mode FROM ws.workspace WHERE id=:id"), {"id": workspace}
                    )
                ).scalar_one()
                if demo:
                    raise AppError(403, "DEMO_READ_ONLY", "Demo workspaces are read only.")
        return user

    return dependency
