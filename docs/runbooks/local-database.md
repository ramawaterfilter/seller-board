# Local PostgreSQL and Redis

WP-03 foundation, 2026-10-12. Synthetic local data only.

For setup plus verification in a normal PowerShell terminal, run from project root:

```powershell
.\scripts\Verify-Local.ps1
```

This starts local services, applies the application migration, creates the test
database if absent, runs the checks and restores previous process environment
settings. It leaves containers running and preserves any existing `.env`.

## Application database

Start Docker Desktop so its Linux engine is available, then run from repository root:

```powershell
uv sync --locked
docker compose up -d postgres redis
Copy-Item .env.example .env
uv run alembic -c api/alembic.ini upgrade head
uv run uvicorn app.main:app --app-dir api/src --host 127.0.0.1 --reload
```

Do not overwrite an existing `.env` with settings you need. The example contains
only synthetic localhost credentials. `healthz` is liveness; `readyz` checks both
services and the foundation migration. Missing services return 503, with no
connection strings or exception details in responses.

## Dedicated integration database

Create a separate test database once on the local compose PostgreSQL server:

```powershell
docker compose exec postgres createdb -U rci_local rci_test_foundation
$env:RCI_TEST_DATABASE_URL='postgresql+psycopg://rci_local:synthetic-local-only@127.0.0.1:5432/rci_test_foundation'
uv run pytest -q
```

The DB fixture rejects remote hosts and database names outside `rci_test...`.
It applies the initial migration, downgrade and re-upgrade, then checks tenant
isolation, permission dimensions/expiry/disabled users, audit immutability and
transactional audit rollback. Test inserts roll back; migration objects remain.
Database checks are skipped with an explicit reason if the test URL is absent.

## Persistence and security boundaries

`ws.workspace` is created now because role/scope/job foreign keys need it; entity,
store, market and period modelling remains WP-04. The tables are migration DDL;
application services use SQLAlchemy transactions and parameterized queries.
Login/MFA/session/permission endpoints are now implemented; see local-authentication.md.
Signup, invitations, privacy processing and job dispatch remain pending.

`app_rw` is NOLOGIN with no superuser or RLS bypass privilege. Runtime explicitly
assumes this role. Workspace context is transaction-local so pooled connections
cannot retain it across requests. `Database.transaction()` must receive a workspace
already authorized by the auth layer; selecting a workspace does not grant
membership. Product/market/function authorization requires all dimensions to match
one unexpired permission row for an active user. Auth dependencies now check membership
before workspace access. An identity policy permits reading only the authenticated
user's permission rows before selecting a workspace.

Audit SELECT is workspace-scoped; INSERT allows a matching workspace or global
authentication evidence. UPDATE/DELETE/TRUNCATE are denied to runtime; database
triggers also guard edits. A default audit partition receives initial events;
monthly partition management belongs to the worker implementation. Callers must
send approved audit metadata, never passwords, tokens or raw provider/customer data.

The isolation model follows [PostgreSQL 16 row security documentation](https://www.postgresql.org/docs/16/ddl-rowsecurity.html).
Migration setup follows [Alembic's tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

The initial migration downgrade preserves all foundation objects/data/protections,
changing only the Alembic revision. Re-upgrade restores the revision idempotently.
Subsequent migrations must follow the same no-destructive-change policy, with their
own reviewed rollback behaviour. This local foundation is not production approved.

## Current environment limitation

Docker was initially unavailable on 2026-10-12. The user subsequently started it,
but this managed session receives permission denied for its named pipe; elevated
access is prohibited by the approval policy. Direct localhost service checks timed
out too. The user then ran Verify-Local.ps1 in a normal terminal successfully:
29 tests passed without skips, lint passed and Alembic reported one head. Both
containers remain running. Live database verification is complete; agent access
was previously denied. In the auth slice, direct localhost PostgreSQL and Redis
access became available; the agent ran all 57 checks, including live API dependency
readiness. Docker pipe access was not required for that run.
