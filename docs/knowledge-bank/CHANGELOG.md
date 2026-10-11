# Session history

## 2026-10-12 — project inspection and first foundation slice

The input folder was a specification/research package without runtime code or
Git metadata. Created the persistent knowledge bank and automatic reading protocol,
draft discovery/freeze artefacts, FastAPI startup/settings/health/errors, local
dependency compose file, toolchain and focused foundation checks.

Baseline: scope register passes; reference runner reports 155/155 vectors pass.
Windows default CP1252 caused the original script runs to fail; rerunning with
UTF-8 environment settings succeeds. Engineering inputs were left unchanged.

Final checks (all exit 0):

- `python engineering/check_register.py` with UTF-8 environment: register v0.3,
  172 features, 193 requirements, 80 screens, 114 calculations, 31 connectors,
  36 work packages, 155 golden vectors. Existing note: CALC-046 is cross-cutting.
- `python engineering/reference_calcs.py` with UTF-8 environment: 155/155 pass.
- `uv sync`: installed 24 packages and generated uv.lock using Python 3.12.10.
- `uv run --no-sync ruff check api/src api/tests --fix`: two import ordering
  issues fixed, zero remaining.
- `uv run --no-sync pytest -q`: 11 passed, one warning in 2.62 seconds. Includes
  both original engineering gates as subprocess checks after document changes.
  Warning is Starlette's use of a deprecated AnyIO BlockingPortal alias.

The managed filesystem denied uv's default user cache on a later invocation;
checks succeeded with UV_CACHE_DIR set to the workspace `.tmp/uv-cache`.
No database containers, migrations, coverage, frontend, Git/CI or deployment
checks were run. Full WP-01 and WP-03 acceptance remains pending.

## 2026-10-12 — WP-03 database, authorization and audit foundation

Added PostgreSQL 16 foundation DDL/migration for identity, workspace scope, sessions,
MFA, audit and durable jobs. Added app_rw grants, workspace RLS, composite role
workspace foreign keys and append-only audit triggers/partition. Added async
database transactions, grant query and transactional audit service. Wired lifespan
resource cleanup and readiness to PostgreSQL migration state and Redis; connection
failures are sanitized and bounded. Added environment example and database runbook.

Validation: uv sync succeeded (SQLAlchemy/Alembic/psycopg/asyncpg/Redis in uv.lock).
25 tests passed, 4 real PostgreSQL tests skipped, one existing Starlette/AnyIO
deprecation warning; latest full run took 1.47 seconds. Ruff passed for application,
tests and Alembic. Alembic has exactly one head, 0001_foundation. Offline upgrade
SQL generation succeeded. Test subprocess gates include register integrity and
155/155 reference vectors.

Live upgrade/downgrade/upgrade and DB security checks NOT RUN: Docker Linux pipe
missing; starting Docker Desktop did not expose the engine and opening its Windows
service was denied. No SQLite or in-memory database substitute was used. No
provider/AWS calls, deployments, commits, pushes or existing work reversions.
Git is now initialized externally (fc7c69f); application files remain untracked.

Next: enable the local Docker engine, verify migration/security on rci_test_foundation,
then implement authentication/MFA/sessions and API authorization dependencies.

## 2026-10-12 — Docker available, agent access denied

The user reported Docker available. `docker info` and `docker ps` now fail with
permission denied on the Docker Desktop Linux named pipe. Elevated docker info
was rejected because sandbox_approval is disabled in the managed approval policy.
Direct localhost checks for 5432/6379 timed out; .env does not exist. No containers
or database migrations were started in this session.

Added scripts/Verify-Local.ps1 for execution in a normal local terminal: starts
only project PostgreSQL/Redis, applies local migration, creates the dedicated
test database if absent, runs checks and restores prior process environment.
It does not overwrite .env, remove data or contact AWS/providers. Script execution
and live database checks remain pending; syntax is checked separately.

## 2026-10-12 — live database verification passed (user terminal)

The user executed Verify-Local.ps1 and supplied its complete success output:
sellerboard-postgres-1 and sellerboard-redis-1 healthy; dependency sync complete;
29 tests passed, none skipped, in 2.68 seconds; Ruff all checks passed;
0001_foundation is the single Alembic head. Script reported local migration and
checks completed, containers remain running.

This resolves the prior live migration/test blocker: all four PostgreSQL checks
ran, including the fixture's upgrade/downgrade/re-upgrade. The existing
Starlette/AnyIO BlockingPortal deprecation warning is non-failing. Evidence is
user terminal output, not an agent rerun. API-server readiness against the real
services, coverage and full WP-03 acceptance are still pending. Next: auth/MFA.

## 2026-10-12 — local authentication and API permissions implemented

Implemented POST auth/login, POST auth/mfa/verify, GET me, GET auth/permissions
and POST auth/logout. Passwords use Argon2id; required TOTP MFA uses encrypted
secrets, one-step drift, replay rejection and serialized verification. Email OTP
is pluggable, keyed/expiring/single-use and tested with an in-memory mailbox;
real delivery defaults to unavailable. Added persistent failures/cooldowns and
Redis account/IP limits. Correct passwords do not reset failed MFA attempts.

Sessions use opaque tokens with DB digests, rotation, expiry, active-user checks,
CSRF-protected logout and HttpOnly cookies. Workspace membership precedes scoped
database access; product/market/function denial and demo write protection are
tested. Added global auth audits, no-store responses and OpenAPI error envelopes.
Fixed shared audit insertion to allocate a sequence ID rather than require
SELECT through RETURNING on a globally unreadable auth event.

Added migration 0002_authentication and applied it to rci_local. Dedicated test
DB fixture exercised upgrade/downgrade/re-upgrade. Agent TCP access to both local
services works now. No AWS, live email/provider calls, credentials or production
resources were used. No commits or pushes; pre-existing work preserved.

Final full command: uv run --no-sync pytest -q --cov=api/src/app
--cov-report=term-missing --tb=short with synthetic RCI_TEST_DATABASE_URL.
Exit 0: 57 passed, none skipped, one existing AnyIO/Starlette deprecation warning,
25.97 seconds. Backend line coverage 97%; auth service 94%, auth API 100%.
Coverage is configured for thread/greenlet concurrency; absent greenlet tracing
initially produced an incorrect low report. Ruff check of api/src, api/tests,
api/alembic and scripts/initialize_local_auth.py passes. Alembic head:
0002_authentication (one). Register gate and all 155 vectors pass in the suite.

Local setup documented in docs/runbooks/local-authentication.md. Interactive
seed helper prompts for a synthetic password, generates git-ignored key/enrollment
files, and preserves an existing user. Syntax and remote/short-password guards
checked; interactive provisioning itself was not exercised end to end. Mypy and
frontend checks were not run. AWS/Vault auth secrets, live email, login/reset UI,
remembered-device policy, self-service enrollment and invitations remain pending.

Next: user invitations / scoped role management, then durable jobs/privacy/telemetry
to complete the remaining WP-03 foundation. All requirements remain UNACCEPTED.

## 2026-10-12 — local frontend foundation

User asked how to access the frontend, then explicitly requested building it.
Added React 18 / strict TypeScript / Vite app, pinned npm dependencies/lockfile,
Node 22 target (.nvmrc), and development server on 127.0.0.1:5173 with a same-origin
/api proxy to port 8000. No backend/CORS/schema changes.

Implemented credential/TOTP forms, MFA challenge handling, cookie session
restoration, workspace chooser, live scoped permission display and CSRF logout.
Credentials, identity and CSRF stay in memory; only theme preference persists.
API requests have 15-second deadlines, no-store and sanitized errors.

Built dark/light responsive shell, seven in-scope navigation groups (unbuilt modules
disabled), channel/period controls, five coloured period tiles, missing-data views,
product/order empty tables, and native modal provenance/data-quality drawer.
Mobile has horizontally scrolling tiles with explicit previous/next controls.
Disconnected preview is available without enrollment and grants no API access.
Workspace names use numbered IDs pending a directory API. All financial values
remain unavailable; no mock money, source facts or client financial calculations.

Commands: npm view for selected dependency versions; npm install --no-audit
--no-fund (72 packages). npm reported esbuild postinstall blocked by its script
policy; build nevertheless succeeded with the installed platform binary. Final
npm run build exited 0: strict TypeScript passed, Vite 6.4.4 transformed 1923 modules
and emitted dist (JS 181.92 kB / gzip 56.70 kB; CSS 16.93 kB / gzip 4.12 kB).
Used installed Node 24.16.0; Node 22 remains the delivery target. No tests were
added/run, no browser/axe journeys, no backend rerun, no deployment/commit/push.

Added docs/runbooks/local-frontend.md, README startup commands, auth guide link,
and continuity notes. Full WP-02/03 acceptance remains pending. Next: requested
browser/axe acceptance checks, WP-03 invitations/roles and WP-04 workspace directory;
then reporting ingestion/calculations. Dashboard currently provides layout only.

## 2026-10-12 — diagnosed local API 503

Read running localhost responses: /api/v1/me returned DATABASE_UNAVAILABLE,
and /api/v1/readyz reported postgres/redis not_configured. Root .env was absent.
Copied .env.example to git-ignored .env with an existence guard. Did not stop the
user's API process; it needs restart to load settings. Local auth key/enrollment
artifacts are absent; interactive initialization remains necessary before login.
No code changes or test runs. Post-restart readiness is not yet confirmed.

## 2026-10-12 — removed authenticator step for current local login

User explicitly requested this temporary change. Added local_password_login setting
(default false) with a startup restriction to local; enabled current .env without
printing its contents or changing other values. Password verification now issues
an opaque cookie session directly when enabled, resets failure state, invalidates
pending challenges, rotates an existing session and records password_local audit.
Password-only sessions store null mfa_verified_at; session lookup accepts them only
while the local override is enabled. No migration or fake MFA timestamp.
MFA routes continue to load encryption keys when needed; password-only login needs
no MFA key. Frontend supports both response types and shows the real session method.

npm run build passed (strict TS + Vite; JS gzip 56.74 kB). Ruff formatting applied
to affected Python files. Backend syntax compilation and Ruff checks are recorded
by the current turn; no tests added/run and no real password/login attempt made.
Restart API after .env changes, then return from MFA to the credentials form.
To restore MFA set RCI_LOCAL_PASSWORD_LOGIN=false and restart; password-only
sessions will be rejected. Updated runbooks, status, architecture and decisions.

## 2026-10-12 — Shopify connection planning

User asked how to connect this app to Shopify. Read CON-05 contract and current
official Shopify app creation/auth/access-scope documentation. New apps use Dev
Dashboard; client credentials grant requires app/store in the same organization,
otherwise choose the appropriate merchant authorization flow. Connector/sync/UI
remain unbuilt, DISC-10/29 are still open, and no real store/credentials/data were
accessed. Proposed first slice is read-only products/inventory/orders sync with
secrets kept on the backend; reporting/profit needs subsequent calculation work.
Store domain and ownership clarification needed before selecting the auth path.
Sources: https://shopify.dev/docs/apps/build/dev-dashboard/create-apps-using-dev-dashboard
and https://shopify.dev/docs/apps/build/authentication-authorization/client-credentials-grant
and https://shopify.dev/docs/api/usage/access-scopes . No code changes/test runs.
