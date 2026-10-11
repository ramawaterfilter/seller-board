# Rama Commerce Intelligence

Unified commerce reporting for Amazon, Shopify and manual B2B, with additional
marketplaces in R2. This repository began as a specification package; application
development started on 2026-10-12. The application is an early foundation, not a
finished reporting product.

Start future sessions with [the knowledge bank](docs/knowledge-bank/STATUS.md).
The authoritative scope is `engineering/scope_register.json` v0.3 rev 2.

## Run locally

Requirements: Python 3.12 and uv. Node 22 is planned for the React application;
there is no frontend implementation yet.

```powershell
uv sync --locked
uv run uvicorn app.main:app --app-dir api/src --host 127.0.0.1 --reload
```

API documentation: http://127.0.0.1:8000/api/v1/docs

`GET /api/v1/healthz` checks API liveness. `GET /api/v1/readyz` checks PostgreSQL
(including the foundation migration) and Redis, returning 503 when either is
unconfigured or unavailable. Authentication endpoints are implemented; business
reporting endpoints and the frontend remain pending.

Configure local dependency containers and apply the foundation migration:

```powershell
docker compose up -d postgres redis
Copy-Item .env.example .env
uv run alembic -c api/alembic.ini upgrade head
```

Compose binds both services to localhost and uses synthetic local database
credentials. PostgreSQL data is retained in a named volume. No AWS resources are
created by these commands.

The migration adds workspace/user/role/permission, session/MFA, audit and durable
job tables. Runtime connections assume `app_rw`, which has workspace row security
and append-only audit permissions. The local synthetic login owns migrations;
deployed application logins must be members of `app_rw` and separate from migration
owners. Credentials for dev/stage are managed outside this repository.

Foundation downgrade retains tables, data and security protections and rolls back
the Alembic revision only. Re-upgrade is idempotent. This follows the project's
additive migration policy; it is not a schema teardown or a way to undo data writes.

## Checks

```powershell
uv run pytest -q
uv run ruff check api/src api/tests api/alembic
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
python engineering/check_register.py
python engineering/reference_calcs.py
```

The pytest subprocess wrapper sets UTF-8 itself. On Windows, set both environment
variables when running the original engineering scripts directly.
If this managed workspace denies access to uv's user cache, set
`$env:UV_CACHE_DIR = Join-Path (Get-Location) '.tmp/uv-cache'` before uv commands.

PostgreSQL and authentication integration checks are skipped unless
`RCI_TEST_DATABASE_URL` is set. Use a separate, synthetic local database named
`rci_test...` (never the
application database). The fixture applies upgrade/downgrade/upgrade and rolls
back foundation test inserts. Auth fixtures retain unique synthetic records.
See [the database runbook](docs/runbooks/local-database.md).

## Current configuration

`RCI_ENV` accepts `local` (default), `test`, `dev`, or `stage`.
`RCI_SECRETS_BACKEND` accepts `devfile` (default), `aws_sm`, or `vault`; local
authentication uses a git-ignored devfile key. AWS/Vault authentication and provider
secret adapters remain pending. Production
is rejected by this scaffold. No provider credentials are needed.

`RCI_DATABASE_URL` is a PostgreSQL psycopg URL (used by migrations; runtime uses
the asyncpg driver against the same database). `RCI_REDIS_URL` uses `redis://` or
`rediss://`. They are loaded from the environment or git-ignored `.env`, hidden in
settings representations, and required in dev/stage. Local/test can omit them;
readiness will then return 503. Readiness probes have a three-second deadline.

## Frontend

From the project root:

```powershell
cd web
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. Use **Preview the interface** without an account,
or start the API and sign in with the initialized local account.
See [frontend setup](docs/runbooks/local-frontend.md) for both terminal commands.
The dashboard shell shows missing data until reporting APIs are implemented.

## Shopify connections

The local **Channels** screen supports separate connections for multiple Shopify
stores. Follow [the multi-store setup guide](docs/runbooks/local-shopify.md) to
select the integration workspace, install a read-only Shopify app, configure
credentials privately in your terminal, verify access and run manual syncs.
The connector imports raw records; profit calculation/reporting is still pending.

## Local API authentication

Follow [the authentication guide](docs/runbooks/local-authentication.md) to initialize
a synthetic user and authenticator, start the API, and exercise login, MFA, session
identity, permissions and logout. MFA is required on every login in this slice.
Email OTP has a pluggable sender and test mailbox; real delivery is not configured.

## Working documents

- [Progress and next task](docs/knowledge-bank/STATUS.md)
- [Architecture and file map](docs/knowledge-bank/ARCHITECTURE.md)
- [Decisions](docs/knowledge-bank/DECISIONS.md)
- [Session history](docs/knowledge-bank/CHANGELOG.md)
- [Draft R0 requirement baseline](docs/requirements/freeze_R0.md)
- [Discovery questions](docs/discovery/open_questions.md)

Read `AGENTS.md` before changing code. Update the knowledge bank before ending
each session. Requirements remain draft and unaccepted until human review.
