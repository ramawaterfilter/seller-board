from uuid import UUID

from sqlalchemy import bindparam, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession


async def append_audit(
    session: AsyncSession,
    *,
    workspace_id: UUID | None,
    actor_user_id: UUID | None,
    action: str,
    trace_id: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    before: dict | None = None,
    after: dict | None = None,
) -> int:
    """Append within the caller's transaction so action and evidence commit together.

    Callers must supply approved metadata only, never passwords, tokens or raw payloads.
    """
    # Global auth rows are insertable but unreadable under RLS; RETURNING would require SELECT.
    event_id = (
        await session.execute(text("SELECT nextval('platform.audit_log_id_seq')"))
    ).scalar_one()
    statement = text("""
        INSERT INTO platform.audit_log
          (id, workspace_id, actor_user_id, actor_kind, action, entity_type, entity_id,
           before, after, trace_id)
        VALUES (:id, :workspace, :actor, :kind, :action, :entity_type, :entity_id,
                :before, :after, :trace)
    """).bindparams(bindparam("before", type_=JSONB), bindparam("after", type_=JSONB))
    await session.execute(
        statement,
        {
            "id": event_id,
            "workspace": workspace_id,
            "actor": actor_user_id,
            "kind": "user" if actor_user_id else "system",
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "before": before,
            "after": after,
            "trace": trace_id,
        },
    )
    return event_id
