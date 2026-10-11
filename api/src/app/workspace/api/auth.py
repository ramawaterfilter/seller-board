from typing import Literal
from uuid import UUID

from app.errors import AppError
from app.platform.audit import append_audit
from app.workspace.api.deps import (
    COOKIE_NAME,
    auth_service,
    check_origin,
    csrf_protected,
    current_user,
    database,
    rate_limit,
    selected_workspace,
)
from app.workspace.service.session import csrf_token, token_hash
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy import text

router = APIRouter(tags=["authentication"])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: SecretStr = Field(min_length=1, max_length=1024)
    method: Literal["totp", "email"] = "totp"


class VerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    challenge_id: UUID
    code: SecretStr

    @field_validator("code")
    @classmethod
    def six_digits(cls, value: SecretStr):
        code = value.get_secret_value()
        if len(code) != 6 or any(c not in "0123456789" for c in code):
            raise ValueError("Enter a six-digit verification code.")
        return value


@router.post("/auth/login")
async def login(body: LoginRequest, request: Request, response: Response):
    check_origin(request)
    await rate_limit(request, email=body.email)
    result = await auth_service(request).login(
        body.email.strip(),
        body.password.get_secret_value(),
        body.method,
        request.state.trace_id,
        request.cookies.get(COOKIE_NAME),
    )
    if isinstance(result, AppError):
        raise result
    if isinstance(result, str):
        return authenticated_response(request, response, result)
    return result


@router.post("/auth/mfa/verify")
async def verify(body: VerifyRequest, request: Request, response: Response):
    check_origin(request)
    await rate_limit(request)
    result = await auth_service(request, require_secrets=True).verify(
        body.challenge_id,
        body.code.get_secret_value(),
        request.state.trace_id,
        request.cookies.get(COOKIE_NAME),
    )
    if isinstance(result, AppError):
        raise result
    return authenticated_response(request, response, result)


def authenticated_response(request: Request, response: Response, token: str):
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        secure=request.app.state.settings.env in {"dev", "stage"},
        samesite="lax",
        path="/",
    )
    return {"status": "authenticated", "csrf_token": csrf_token(token)}


@router.get("/me")
async def me(request: Request, user=Depends(current_user)):
    async with database(request).identity_transaction(user["id"]) as session:
        workspaces = (
            (
                await session.execute(
                    text("""
            SELECT DISTINCT workspace_id FROM ws.permission_scope WHERE user_id=:user
              AND (expires_at IS NULL OR expires_at>now()) ORDER BY workspace_id
        """),
                    {"user": user["id"]},
                )
            )
            .scalars()
            .all()
        )
    workspace_labels = []
    for workspace_id in workspaces:
        async with database(request).transaction(workspace_id) as session:
            row = (
                (
                    await session.execute(
                        text("SELECT id,name,demo_mode FROM ws.workspace WHERE id=:id"),
                        {"id": workspace_id},
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is not None:
                workspace_labels.append(dict(row))
    return {
        **user,
        "workspace_ids": workspaces,
        "workspaces": workspace_labels,
        "csrf_token": csrf_token(request.cookies[COOKIE_NAME]),
    }


@router.get("/auth/permissions")
async def permissions(
    request: Request, workspace=Depends(selected_workspace), user=Depends(current_user)
):
    async with database(request).transaction(workspace) as session:
        grants = (
            (
                await session.execute(
                    text("""
            SELECT function_code,product_scope,market_scope FROM ws.permission_scope
            WHERE workspace_id=:workspace AND user_id=:user
              AND (expires_at IS NULL OR expires_at>now())
            ORDER BY function_code,product_scope,market_scope
        """),
                    {"workspace": workspace, "user": user["id"]},
                )
            )
            .mappings()
            .all()
        )
    return {"workspace_id": workspace, "grants": [dict(row) for row in grants]}


@router.post("/auth/logout", status_code=204)
async def logout(request: Request, response: Response, user=Depends(csrf_protected)):
    async with database(request).sessions.begin() as session:
        await session.execute(
            text("UPDATE ws.session SET revoked_at=now() WHERE token_hash=:hash"),
            {"hash": token_hash(request.cookies[COOKIE_NAME])},
        )
        await append_audit(
            session,
            workspace_id=None,
            actor_user_id=user["id"],
            action="logout.success",
            trace_id=request.state.trace_id,
        )
    response.delete_cookie(
        COOKIE_NAME,
        path="/",
        secure=request.app.state.settings.env in {"dev", "stage"},
        httponly=True,
        samesite="lax",
    )
