"""Real PostgreSQL checks; RCI_TEST_DATABASE_URL must name a disposable local test DB."""
import asyncio
import os
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.platform.audit import append_audit
from app.workspace.service.rbac import permitted
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

ROOT = Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.db


@pytest.fixture(scope="module")
def engine():
    dsn = os.environ.get("RCI_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("RCI_TEST_DATABASE_URL is not configured; needs real PostgreSQL 16")
    url = make_url(dsn)
    assert url.host in {"localhost", "127.0.0.1"} and url.database.startswith("rci_test")
    assert url.drivername == "postgresql+psycopg"
    engine = create_engine(url, hide_parameters=True)
    config = Config(str(ROOT / "api/alembic.ini"))
    old = os.environ.get("RCI_DATABASE_URL")
    os.environ["RCI_DATABASE_URL"] = dsn
    try:
        command.upgrade(config, "head")
        command.downgrade(config, "-1")
        command.upgrade(config, "head")
        yield engine
    finally:
        if old is None:
            os.environ.pop("RCI_DATABASE_URL", None)
        else:
            os.environ["RCI_DATABASE_URL"] = old
        engine.dispose()


@pytest.fixture
def seeded(engine):
    with engine.connect() as connection:
        transaction = connection.begin()
        workspace, other_workspace, user, role = (uuid4() for _ in range(4))
        connection.execute(text("INSERT INTO ws.workspace(id, name) VALUES (:id, 'SYNTH')"),
                           [{"id": workspace}, {"id": other_workspace}])
        connection.execute(text('INSERT INTO ws."user"(id,email,display_name) '
                                "VALUES (:id,:email,'SYNTH')"),
                           {"id": user, "email": f"{user}@example.test"})
        connection.execute(text("INSERT INTO ws.role(id,workspace_id,name) "
                                "VALUES (:id,:ws,'viewer')"), {"id": role, "ws": workspace})
        connection.execute(text("SET LOCAL ROLE app_rw"))
        connection.execute(text("SELECT set_config('app.workspace_id', :id, true)"),
                           {"id": str(workspace)})
        try:
            yield connection, workspace, other_workspace, user, role
        finally:
            transaction.rollback()


@pytest.mark.req("REQ-006")
def test_workspace_rls_and_role_foreign_key(seeded):
    connection, workspace, other, _, role = seeded
    rows = connection.execute(text("SELECT id FROM ws.workspace")).scalars().all()
    assert rows == [workspace]
    with pytest.raises(DBAPIError):
        with connection.begin_nested():
            connection.execute(text("UPDATE ws.role SET workspace_id=:other WHERE id=:role"),
                               {"other": other, "role": role})
    connection.execute(text("SELECT set_config('app.workspace_id', '', true)"))
    assert connection.execute(text("SELECT count(*) FROM ws.role")).scalar_one() == 0


@pytest.mark.req("REQ-160")
def test_audit_is_append_only(seeded):
    connection, workspace, _, _, _ = seeded
    connection.execute(text("INSERT INTO platform.audit_log"
                            "(workspace_id,actor_kind,action,trace_id) "
                            "VALUES (:ws,'system','SYNTH','SYNTH')"), {"ws": workspace})
    for statement in ["UPDATE platform.audit_log SET action='changed'",
                      "DELETE FROM platform.audit_log", "TRUNCATE platform.audit_log",
                      "TRUNCATE platform.audit_log_default"]:
        with pytest.raises(DBAPIError):
            with connection.begin_nested():
                connection.execute(text(statement))
    assert connection.execute(text("SELECT count(*) FROM platform.audit_log")).scalar_one() == 1


class SessionAdapter:
    """Run the async service query against the real rollback-scoped sync transaction."""
    def __init__(self, connection):
        self.connection = connection

    async def execute(self, statement, parameters=None):
        return self.connection.execute(statement, parameters)


@pytest.mark.req("REQ-006")
def test_permission_dimensions_expiry_and_status(seeded):
    connection, workspace, other, user, role = seeded
    connection.execute(text("""
        INSERT INTO ws.permission_scope(workspace_id,user_id,role_id,function_code,
                                        product_scope,market_scope)
        VALUES (:ws,:user,:role,'profit.read','product:SYNTH','country:IN')
    """), {"ws": workspace, "user": user, "role": role})
    session = SessionAdapter(connection)

    def allowed(ws=workspace, function="profit.read", product="product:SYNTH", market="country:IN"):
        return asyncio.run(permitted(session, user, ws, function, product, market))

    assert allowed()
    assert not allowed(ws=other)
    assert not allowed(market="country:UK")
    assert not allowed(product="product:OTHER")
    assert not allowed(function="users.manage")
    connection.execute(text("UPDATE ws.permission_scope SET expires_at=now()-interval '1 second'"))
    assert not allowed()
    connection.execute(text("UPDATE ws.permission_scope SET expires_at=NULL"))
    connection.execute(text('UPDATE ws."user" SET status=\'disabled\' WHERE id=:id'), {"id": user})
    assert not allowed()


@pytest.mark.req("REQ-160")
def test_audit_service_rolls_back_with_action(seeded):
    connection, workspace, _, user, _ = seeded
    nested = connection.begin_nested()
    session = SessionAdapter(connection)
    event = asyncio.run(append_audit(session, workspace_id=workspace, actor_user_id=user,
                                   action="SYNTH", trace_id="SYNTH", after={"status": "active"}))
    assert connection.execute(text("SELECT id FROM platform.audit_log WHERE id=:id"),
                              {"id": event}).scalar_one() == event
    nested.rollback()
    assert connection.execute(text("SELECT count(*) FROM platform.audit_log")).scalar_one() == 0
