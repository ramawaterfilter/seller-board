from typing import Literal
from uuid import UUID, uuid4

from app.errors import AppError
from app.ingestion.connectors.shopify.client import API_VERSION, shop_domain
from app.ingestion.service.credentials import remove_credentials
from app.ingestion.service.shopify import (
    authorize,
    connection,
    probe,
    public_connection,
    run_sync,
    update_config,
)
from app.platform.audit import append_audit
from app.workspace.api.deps import csrf_protected, current_user, database, selected_workspace
from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/connectors/shopify", tags=["Shopify connections"])


class CreateConnection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shop_domain: str = Field(max_length=80)
    country: str = Field(pattern=r"^[A-Z]{2}$")
    auth_mode: Literal["client_credentials", "offline_token"]

    @field_validator("shop_domain")
    @classmethod
    def valid_domain(cls, value):
        return shop_domain(value)


@router.get("")
async def list_connections(
    request: Request, workspace=Depends(selected_workspace), user=Depends(current_user)
):
    async with database(request).transaction(workspace) as session:
        rows = (
            (
                await session.execute(
                    text("""
            SELECT c.* FROM ing.connector c WHERE c.workspace_id=:ws AND EXISTS (
              SELECT 1 FROM ws.permission_scope p WHERE p.workspace_id=c.workspace_id
                AND p.user_id=:user AND p.function_code IN ('*','connectors.manage')
                AND p.product_scope='*'
                AND p.market_scope IN ('*','country:'||(c.config->>'country'))
                AND (p.expires_at IS NULL OR p.expires_at>now()))
            ORDER BY c.created_at,c.id
        """),
                    {"ws": workspace, "user": user["id"]},
                )
            )
            .mappings()
            .all()
        )
        demo = (
            await session.execute(
                text("SELECT demo_mode FROM ws.workspace WHERE id=:ws"), {"ws": workspace}
            )
        ).scalar_one()
    return {"connections": [public_connection(r) for r in rows], "demo_mode": demo}


@router.post("", status_code=201)
async def create_connection(
    body: CreateConnection,
    request: Request,
    workspace=Depends(selected_workspace),
    user=Depends(csrf_protected),
):
    connector_id = uuid4()
    try:
        async with database(request).transaction(workspace) as session:
            await authorize(session, workspace, user["id"], body.country, write=True)
            await session.execute(
                text("""
                INSERT INTO ing.connector(id,workspace_id,connector_code,api_version,
                  config,credential_ref)
                VALUES (:id,:ws,'CON-05',:version,:config,:ref)
            """).bindparams(bindparam("config", type_=JSONB)),
                {
                    "id": connector_id,
                    "ws": workspace,
                    "version": API_VERSION,
                    "config": body.model_dump(),
                    "ref": f"devfile:shopify/{connector_id}",
                },
            )
            await append_audit(
                session,
                workspace_id=workspace,
                actor_user_id=user["id"],
                action="shopify.connection_created",
                trace_id=request.state.trace_id,
                entity_type="connector",
                entity_id=str(connector_id),
                after={"mode": "read"},
            )
            row = await connection(session, workspace, user["id"], connector_id)
    except IntegrityError:
        raise AppError(
            409, "SHOPIFY_ALREADY_ADDED", "This store is already added to the workspace."
        ) from None
    return public_connection(row)


@router.post("/{connector_id}/check")
async def check_connection(
    connector_id: UUID,
    request: Request,
    workspace=Depends(selected_workspace),
    user=Depends(csrf_protected),
):
    db = database(request)
    async with db.transaction(workspace) as session:
        row = await connection(session, workspace, user["id"], connector_id, write=True)
    try:
        _, metadata = await probe(request.app.state.settings, row)
    except AppError as exc:
        async with db.transaction(workspace) as session:
            await connection(session, workspace, user["id"], connector_id, write=True)
            await session.execute(
                text("""UPDATE ing.connector SET last_error=:err,last_error_at=now(),
              status=CASE WHEN :err='CONNECTOR_REVOKED' THEN 'revoked' ELSE status END
              ,revoked_at=CASE WHEN :err='CONNECTOR_REVOKED' THEN now() ELSE revoked_at END
              WHERE id=:id"""),
                {"err": exc.code, "id": connector_id},
            )
            await append_audit(
                session,
                workspace_id=workspace,
                actor_user_id=user["id"],
                action="shopify.check_failed",
                trace_id=request.state.trace_id,
                entity_type="connector",
                entity_id=str(connector_id),
                after={"error_code": exc.code},
            )
        raise
    async with db.transaction(workspace) as session:
        current = await connection(
            session, workspace, user["id"], connector_id, write=True, lock=True
        )
        if current["revision"] != row["revision"]:
            raise AppError(
                409, "REVISION_CONFLICT", "Connection changed during verification. Try again."
            )
        await update_config(session, workspace, connector_id, {**current["config"], **metadata})
        await append_audit(
            session,
            workspace_id=workspace,
            actor_user_id=user["id"],
            action="shopify.connection_verified",
            trace_id=request.state.trace_id,
            entity_type="connector",
            entity_id=str(connector_id),
        )
        return public_connection(await connection(session, workspace, user["id"], connector_id))


@router.post("/{connector_id}/sync", status_code=202)
async def start_sync(
    connector_id: UUID,
    request: Request,
    background: BackgroundTasks,
    workspace=Depends(selected_workspace),
    user=Depends(csrf_protected),
):
    db, job_id = database(request), uuid4()
    async with db.transaction(workspace) as session:
        row = await connection(session, workspace, user["id"], connector_id, write=True, lock=True)
        if row["status"] != "connected" or row["kill_switch"]:
            raise AppError(
                409, "SHOPIFY_NOT_CONNECTED", "Verify an active connection before syncing."
            )
        # Interrupted in-process jobs can be retried manually after their execution deadline.
        await session.execute(
            text("""UPDATE ing.sync_job SET state='failed',error_code='SYNC_INTERRUPTED',
            finished_at=now() WHERE connector_id=:id AND state IN ('queued','running')
              AND queued_at<now()-interval '15 minutes'"""),
            {"id": connector_id},
        )
        active = (
            await session.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM ing.sync_job WHERE connector_id=:id "
                    "AND state IN ('queued','running'))"
                ),
                {"id": connector_id},
            )
        ).scalar_one()
        if active:
            raise AppError(409, "SHOPIFY_SYNC_ACTIVE", "This store already has a sync in progress.")
        await session.execute(
            text(
                "INSERT INTO ing.sync_job(id,workspace_id,connector_id,trace_id) "
                "VALUES (:id,:ws,:connector,:trace)"
            ),
            {
                "id": job_id,
                "ws": workspace,
                "connector": connector_id,
                "trace": request.state.trace_id,
            },
        )
        await append_audit(
            session,
            workspace_id=workspace,
            actor_user_id=user["id"],
            action="shopify.sync_queued",
            trace_id=request.state.trace_id,
            entity_type="connector",
            entity_id=str(connector_id),
            after={"job_id": str(job_id)},
        )
    # shortcut: local manual jobs run in-process; move to arq before unattended/large-store use.
    background.add_task(
        run_sync,
        db,
        request.app.state.settings,
        workspace,
        user["id"],
        connector_id,
        job_id,
        request.state.trace_id,
    )
    return {"job_id": job_id, "state": "queued"}


@router.get("/{connector_id}/jobs")
async def jobs(
    connector_id: UUID,
    request: Request,
    workspace=Depends(selected_workspace),
    user=Depends(current_user),
):
    async with database(request).transaction(workspace) as session:
        await connection(session, workspace, user["id"], connector_id)
        rows = (
            (
                await session.execute(
                    text("""SELECT id,state,queued_at,started_at,finished_at,
          produced_raw_count,error_code,params FROM ing.sync_job WHERE connector_id=:id
          ORDER BY queued_at DESC LIMIT 10"""),
                    {"id": connector_id},
                )
            )
            .mappings()
            .all()
        )
    return {"jobs": [dict(r) for r in rows]}


class ConnectionState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["paused", "disconnected", "pending_auth"]
    revision: int = Field(ge=1)


@router.post("/{connector_id}/state")
async def change_state(
    connector_id: UUID,
    body: ConnectionState,
    request: Request,
    workspace=Depends(selected_workspace),
    user=Depends(csrf_protected),
):
    async with database(request).transaction(workspace) as session:
        row = await connection(session, workspace, user["id"], connector_id, write=True, lock=True)
        if row["revision"] != body.revision:
            raise AppError(
                409, "REVISION_CONFLICT", "Connection changed. Refresh before trying again."
            )
        if body.status == "disconnected":
            remove_credentials(request.app.state.settings, connector_id)
        await session.execute(
            text("""UPDATE ing.connector SET status=:status,revision=revision+1,
          updated_at=now() WHERE id=:id"""),
            {"status": body.status, "id": connector_id},
        )
        await append_audit(
            session,
            workspace_id=workspace,
            actor_user_id=user["id"],
            action="shopify.state_changed",
            trace_id=request.state.trace_id,
            entity_type="connector",
            entity_id=str(connector_id),
            after={"status": body.status},
        )
        return public_connection(await connection(session, workspace, user["id"], connector_id))
