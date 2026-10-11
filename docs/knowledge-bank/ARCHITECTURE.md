# Architecture and file map

Read STATUS.md first. Last updated: 2026-10-12.

## Product and authority

Rama / Phoenix Commerce Intelligence combines channel profit reporting, COGS,
fees/refunds, inventory, B2B and consolidated reporting. R1 focuses on Amazon.in,
Shopify India and manual B2B. R2 adds all Amazon marketplaces, Walmart, eBay and
TikTok Shop. Marketing modules are omitted; ad spend remains a cost input only.

Authoritative inputs, read only unless change control authorizes edits:

| File | Read it when |
|---|---|
| engineering/scope_register.json | Resolving IDs, scope, releases, acceptance |
| engineering/golden_vectors.json | Implementing financial calculations |
| docs/05_Engineering_Specification.md | Implementing the affected context/API/schema |
| docs/03_UI_UX_Atlas.md | Implementing a screen or interaction |
| integration/connector_contracts.md | Implementing a provider adapter |
| prompts/08_Codex_Prompt_Pack.md | Selecting the next work package and its gates |
| docs/12_Developer_Handoff_Codex_AWS.md | Delivery/deployment and human gates |

Prefer Markdown documents over DOCX copies. Historical briefs have older counts;
register v0.3 rev 2 has 172 features, 193 requirements, 155 golden vectors.

## Planned stack

Python 3.12 / FastAPI; SQLAlchemy 2 / Alembic; PostgreSQL 16 with one schema per
context; Redis 7 / arq with durable jobs mirrored in Postgres; React 18 / strict
TypeScript / Vite with Node 22. Modular monolith, separate API/worker/scheduler
entrypoints. AWS Mumbai primary, Hyderabad DR; human production gates.

## Implemented files

| Path | Responsibility |
|---|---|
| api/src/app/main.py | App factory, trace middleware, router registration |
| api/src/app/settings.py | Validated environment settings; rejects prod |
| api/src/app/errors.py | HTTP, validation and unexpected error envelopes |
| api/src/app/platform/health.py | Liveness; PostgreSQL migration and Redis readiness |
| api/src/app/platform/database.py | Async SQLAlchemy engine as app_rw; transaction-local workspace scope |
| api/src/app/platform/audit.py | Transactional append-only audit insertion |
| api/src/app/workspace/service/rbac.py | Active user, function/product/market and expiry grant check |
| api/src/app/workspace/service/auth.py | Password/MFA challenges, cooldowns, Redis limiter, audit |
| api/src/app/workspace/service/totp.py | RFC 6238 code generation / drift / replay checking |
| api/src/app/workspace/service/auth_secrets.py | Local devfile encryption and keyed OTP digest |
| api/src/app/workspace/service/email_otp.py | Sender interface and unavailable Null sender |
| api/src/app/workspace/service/session.py | Opaque token hashing, issue/expiry/current identity |
| api/src/app/workspace/api/auth.py | Login, verify, me, permissions and logout routes |
| api/src/app/workspace/api/deps.py | Session, CSRF, origin, membership, permission/demo guards |
| api/alembic/versions/0001_foundation.py / .sql | Initial schema, RLS, grants and audit triggers |
| api/alembic/versions/0002_authentication.py / .sql | Failure/challenge/session state and identity scope policy |
| api/alembic.ini / api/alembic/env.py | Migrations using a separate owner connection |
| api/tests/platform/test_foundation.py | Startup/errors/settings checks |
| api/tests/golden/test_register_integrity.py | Reference gates and instruction parity |
| pyproject.toml / uv.lock | Python dependencies and tool configuration |
| docker-compose.yml / .env.example | Local PostgreSQL / Redis and synthetic connection configuration |
| AGENTS.md | Root project instructions plus knowledge bank reading protocol |
| api/, web/, infra/ nested AGENTS.md | Supplied context rules; mostly no runtime yet |
| docs/runbooks/local-database.md | Setup and dedicated real PostgreSQL test instructions |
| docs/runbooks/local-authentication.md | Local enrollment and API login walkthrough |
| scripts/initialize_local_auth.py | Interactive synthetic user/demo workspace provisioning |
| web/package.json / package-lock.json / tsconfig.json | Pinned React 18 / Vite / strict TS toolchain |
| web/vite.config.ts | Loopback port 5173, strict port, same-origin /api development proxy |
| web/src/App.tsx | Session restoration, workspace selection, permissions/settings and logout |
| web/src/api.ts | Cookie requests, no-store, deadlines and sanitized API error handling |
| web/src/pages/Login.tsx | Password/TOTP form; no credentials persisted |
| web/src/pages/Dashboard.tsx | Missing-data dashboard shell and native modal lineage drawer |
| web/src/components/ui.tsx / web/src/design/ | Shared UI, token-only colours, responsive dark/light styles |
| docs/runbooks/local-frontend.md | Port 5173 access, setup and implementation limits |
| api/alembic/versions/0003_shopify_connections.py / .sql | Connector/jobs/raw receipt tables, workspace RLS and append-only raw |
| api/src/app/ingestion/api/shopify.py | Connection CRUD/state, verification and manual job endpoints |
| api/src/app/ingestion/connectors/shopify/client.py / queries.py | Strict domain/HTTPS, no redirects, read queries, tokens/throttling |
| api/src/app/ingestion/service/shopify.py | Scope/demo authorization, PII allow-list, hashed raw import and job execution |
| api/src/app/ingestion/service/credentials.py | Local encrypted secret reference resolution, workspace/domain binding |
| scripts/initialize_shopify_workspace.py | Synthetic local non-demo integration workspace with scoped admin access |
| scripts/setup_shopify_credentials.py | Human-only hidden credential prompts; no agent use with real credentials |
| web/src/pages/Channels.tsx / components/When.tsx | Multi-store connection cards, actions/jobs polling and timezone rendering |
| docs/runbooks/local-shopify.md | Five-store installation/auth/setup walkthrough and current limits |

Foundation persistence uses explicit migration DDL and parameterized SQLAlchemy
service queries. Migrations use psycopg sync; runtime uses asyncpg (Windows async
event loop support). The initial migration includes ws.workspace because the
role/scope/job records need its foreign key; other entity modelling remains pending.
Database.transaction() sets workspace context locally. Auth membership checks use
identity_transaction() first, with a SELECT policy allowing only the signed-in
user's permission rows. Global auth audit events are insert-only for runtime;
append_audit allocates a sequence ID without RETURNING to preserve that boundary.

Auth routes: POST /api/v1/auth/login, POST /api/v1/auth/mfa/verify,
GET /api/v1/me, GET /api/v1/auth/permissions (X-Workspace-Id), and
POST /api/v1/auth/logout (X-CSRF-Token). Cookie rci_session contains an opaque token;
DB stores its digest. MFA is required by default; no remembered-device bypass.
The user requested temporary local password-only login. RCI_LOCAL_PASSWORD_LOGIN
defaults false and is only allowed in local. Those sessions have null
mfa_verified_at, are rejected when the override is disabled, and expose their
authentication_method through /me. Cookie/CSRF/expiry/RBAC safeguards still apply.
AWS/Vault auth key loading and real email delivery remain unavailable/fail closed.

Frontend uses Vite's same-origin /api proxy in local development; no API CORS
change. Deployment must configure its own same-origin API routing and SPA fallback.
URL paths: /auth/login, /workspaces, /dashboard and /settings; auth gating uses
the server's /me identity and /auth/permissions grants. Workspace selection stays
in memory and is repeated after a reload. No PII/session/CSRF/challenge values in
browser persistent storage; only theme is stored. Preview grants no API access.
Dashboard amounts remain missing; no financial arithmetic or mock reporting facts.

Channels route /settings/connectors calls /api/v1/connectors/shopify. Each store
has an ing.connector row with country-scoped connectors.manage checks and its own
credential_ref. Config holds metadata only; devfile credential envelopes are bound
to connector/workspace/domain and encrypted under .tmp/connector-secrets. Adapter
is local-only. Auth modes: client_credentials (own organization) or offline_token
(human-provisioned authorized installation). No built-in OAuth install flow yet.
Verify probes read scopes and store identity/country/currency/timezone; no write
scopes accepted. Store directory foreign key is deferred (nullable store_id).

Manual sync uses FastAPI BackgroundTasks with persistent ing.sync_job state, not
arq. Paginated products/variants/inventory/last-60-day orders and nested records
are sanitized before append-only ing.raw_payload insert. ing.raw_receipt provides
cross-partition idempotency; inventory observation versions use job IDs, order
lines use parent update times. Jobs have deadline/partial failure and manual retry
after stale interruption; no scheduler/automatic resume. Other WP-05/12 storage,
normalization, bulk operations, webhooks and payment/refund reconciliation pending.

## Rules to carry forward

Money uses Decimal, NUMERIC(18,4) plus currency, and 4 decimal place wire strings.
Missing/stale data stays null with flags. Provider ingestion is read only, raw-first
and append-only. Workspace/product/market authorization defaults to deny. Posted
B2B documents are immutable with maker/checker separation. No tax-authority filing
or generated compliance identifiers. No real customer data or credentials in agent
tasks or fixtures. The existing reference runner is fixture arithmetic, not proof
of application financial correctness.
