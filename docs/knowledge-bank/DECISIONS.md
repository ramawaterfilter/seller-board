# Decisions

## 2026-10-12 — start local implementation

The user requested project inspection, implementation and a persistent knowledge
bank. This authorizes ordinary local development. The existing cloud/GitHub
handoff remains the later delivery plan. No repository was initialized or pushed;
there was no .git directory at intake.

Use the supplied stack and current register. Preserve all requirements as
UNACCEPTED and the WP-01 freeze as DRAFT. Draft source inventories and discovery
documents do not prove live API facts or close human discovery questions.

Start WP-03 with API startup/settings/errors/health, an independent local slice.
Do not claim the full foundation or WP-01 is complete. Auth, RBAC and durable
storage come next; provider access and CA approvals remain human dependencies.

Initial readiness returned 503 pending adapters. The persistence slice now probes
the database migration and Redis and returns 503 unless both respond. This is
dependency health only, not evidence that business features or authentication exist.

Keep supplied engineering scripts unchanged. Use PYTHONUTF8=1 and
PYTHONIOENCODING=utf-8 for their Windows runs; wrappers set both explicitly.

Root AGENTS.md and prompts/AGENTS.md remain identical; both include the continuity
protocol so later bootstrap copies preserve it. Knowledge notes are navigation,
not a replacement for task-specific code and specification review.

## 2026-10-12 — WP-03 persistence slice

Use SQLAlchemy with asyncpg for runtime and psycopg for sync migrations. This avoids
psycopg's Windows async loop constraints. Runtime connections always assume the
restricted app_rw role; migration connections retain schema-owner permissions.
Dev/stage require explicit PostgreSQL/Redis URLs; missing local/test URLs produce
unavailable readiness. Connection values are hidden in Settings representations.

Create ws.workspace from the supplied DDL now to satisfy role/scope/job foreign
keys. Leave legal entities, stores, markets and periods for WP-04. Auth routes,
worker dispatch and privacy processing are separate remaining slices of WP-03.

Downgrade of the first migration preserves tables/data/security and only removes
the Alembic revision; re-upgrade is idempotent. This is the chosen interpretation
of the supplied additive-only / no-DROP rule, documented for human review. It does
not claim destructive rollback or reverse application writes. Audit starts with a
default partition; scheduled monthly partition maintenance is pending worker work.

## 2026-10-12 — user requested frontend implementation

Build a local React/Vite slice now in response to the user's explicit frontend
request, before the remaining foundation tasks. Preserve scope and DRAFT acceptance.
Use existing authentication APIs without changing cookie/origin protections.
Vite port 5173 proxies /api to port 8000; no broad CORS and no hosted deployment.
Use React 18, strict TypeScript, Lucide and token styles; native labelled controls
and a native modal dialog avoid extra component/router dependencies for this slice.
Full shadcn/Tailwind system rollout remains later WP-02 work.

Offer an explicitly disconnected interface preview for viewing before enrollment.
It does not create a session or bypass API authorization. Missing source/financial
data remains missing, and unbuilt modules are disabled. Do not fabricate workspace
names: the existing /me endpoint supplies IDs only. Settings lists real permission
grants; profit visibility requires profit.read, with server checks authoritative.
Node 22 stays the target; allow installed Node 24 for local development (build passed).

Live database verification remains blocked by unavailable Docker daemon/service
access. Keep the real PostgreSQL tests explicitly skipped until the engine is ready;
do not claim database security or migration round trip has passed from offline SQL.

## 2026-10-12 — authentication slice

Direct localhost service access became available. Implement local/test authentication
now; AWS/Vault key adapters and a real email sender are later work, not fake successes.
Use argon2-cffi defaults (Argon2id), RFC 6238 TOTP with drift/replay tracking, Fernet
for enrolled secrets, and keyed email digests bound to single-use challenges.
The local helper prompts a human for a synthetic password; keys/enrollment artifacts
stay in .tmp. No secret key, user password or OTP is returned by login APIs or logged.

Always require MFA in this slice. Remember-device and reset/enrollment UI remain
pending. Sessions use opaque random tokens and DB hashes, with 12-hour idle/seven-day
absolute limits. Only MFA success resets account failures. Re-login rotates the
session, logout revokes it, and unsafe requests need CSRF plus allowed Origin.

The rate limiter uses direct peer addresses; forwarded headers are untrusted until
a proxy configuration is reviewed. Throttling fails closed if Redis is unavailable.
Counter/audit updates commit on authentication rejection rather than rolling back.

Global authentication audits cannot be SELECTed by runtime. Fix the shared append
helper to allocate an ID before INSERT instead of broadening its SELECT policy for
RETURNING. Membership lookup uses a transaction-local authenticated actor scope
policy; business workspace context is selected only after checking membership.

Coverage must declare thread and greenlet concurrency for SQLAlchemy async execution;
without greenlet tracing it incorrectly missed executed authentication paths.

## 2026-10-12 — temporary local password-only login

User explicitly requested removing the authenticator step for now. Add opt-in
RCI_LOCAL_PASSWORD_LOGIN (default false), allowed only in local, and enable in
the current git-ignored .env. Retain enrolled secrets/MFA paths for restoring it.
Do not impersonate MFA verification: password-only sessions have null
mfa_verified_at and require the local flag to authenticate. Audit records use
password_local. Existing cookie, CSRF, throttling, expiry and authorization apply.
Frontend accepts either authenticated login or an MFA challenge; Settings reflects
the actual session authentication method. This is a local exception, not acceptance
of the draft MFA requirement or a change to dev/stage policy.

## 2026-10-12 — multi-store Shopify local slice

User requested Shopify connection and clarified five different stores. Build a
local manual integration slice now while keeping full WP-05/12 acceptance pending.
Multiple ing.connector rows per workspace; never a global token/assumed store.
Use verified 2026-07 read queries and reject write scopes. Human terminal enrolls
encrypted credentials, bound to workspace/store; no secrets in frontend/config.
Support own-organization client credentials and a manually provisioned offline
token; other-merchant OAuth installer/refresh and cloud key adapters remain pending.
Store ownership/domains/approval outcomes unknown; fail closed instead of guessing.

Create a separate local integration workspace for the synthetic user, preserving
the demo write guard. Use existing connectors.manage with full product and matching
country/wildcard grants. Country/currency/timezone verified via Shopify probe.
Deferred nullable store_id integration until WP-04 directory/legal entities exist.

Manual jobs persist status in Postgres but execute in the API process with deadlines;
move to arq/bulk before unattended or large-store use. No claimed automatic sync,
webhooks/Payments or profit. Append sanitized records with partition-independent
idempotency receipts; retain partial imports explicitly on failure. Snapshot
inventory versions use job IDs to retain reversions; order lines use parent time.
