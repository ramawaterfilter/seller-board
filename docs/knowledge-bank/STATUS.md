# Project status — read first each session

Last updated: 2026-10-12. Application development started; no work package has
passed its complete acceptance gate. Scope remains v0.3 rev 2 DRAFT / UNACCEPTED.

## Completed locally

- Inspected the handoff, stack, register, execution order and project rules.
- Copied root and nested agent instructions; added a knowledge bank continuity rule.
- Drafted WP-01 source inventory, owner/question register, R0 acceptance baseline
  and architecture record. Human review and freeze remain pending.
- Started WP-03: FastAPI app, validated settings, trace IDs, sanitized error
  responses, live dependency readiness, locked Python toolchain.
- Added initial PostgreSQL migration: workspace, users, roles/scopes, sessions,
  MFA, append-only partitioned audit and durable job records. Runtime database
  connections use app_rw; workspace tables have row security.
- Added transaction-scoped SQLAlchemy access, audit append service and scoped
  authorization query, now wired into authentication and permissions routes.
- Added password login (Argon2id), required MFA (TOTP / pluggable email sender),
  encrypted TOTP secrets, expiring/single-use challenges and replay protection.
- Added hashed server sessions, 12-hour idle / seven-day absolute expiry, rotation,
  CSRF-protected logout, workspace membership and product/market/function checks.
- Added migration 0002_authentication, cooldowns/throttling, auth audit events,
  no-store responses, demo write guard and local synthetic initialization helper.
- Added local PostgreSQL 16 / Redis 7 compose configuration and run instructions.
- Added React 18 / strict TypeScript / Vite frontend with TOTP login, cookie session
  restoration, workspace selection, scoped permissions and CSRF logout.
- Added responsive dark/light dashboard shell: channel/period filters, period tiles,
  view tabs, record table empty states, data-quality/lineage drawer and disconnected
  interface preview. No financial values or source records are fabricated.
- Added local multi-store CON-05 Shopify connections: Channels page, private terminal
  credential enrollment, per-store verification, manual paginated product/variant/
  inventory/recent-order import, jobs/status, pause/disconnect and sanitized raw storage.
- Added migration 0003_shopify_connections with workspace RLS, append-only raw records
  and partition-independent idempotency receipts. Applied to local application DB.
- Created a separate non-demo integration workspace for the synthetic local account:
  84b41ae2-7ef9-46d9-9b02-57711c5f5b6d. Existing demo remains read only.

## Verification

Shopify slice: seven read GraphQL queries validated against 2026-07 (one deprecated
Shop.billingAddress warning). Frontend build passed. Migration upgrade applied;
single head 0003_shopify_connections. Local integration workspace helper ran
successfully after fixing script import paths. No agent live provider requests or
credential enrollment. Security/sync tests, migration round trip and browser/axe
checks for this slice remain pending; older backend test counts do not cover it.

User requested temporary removal of authenticator login. Added opt-in local-only
RCI_LOCAL_PASSWORD_LOGIN and enabled it in current .env. Backend returns a session
after password verification; frontend skips the MFA screen on that response.
MFA remains the default; dev/stage reject the override. Password-only sessions
have no MFA verification timestamp and become unusable when the override is off.

Local startup follow-up: /me returned DATABASE_UNAVAILABLE (503) and /readyz
reported both services not_configured. Root .env was absent; copied .env.example
to .env without overwriting existing configuration. The running API must be
restarted to load settings; post-restart readiness remains pending. Local auth
key/enrollment artifacts are also absent; initialize before attempting login.

Scope register passes and 155/155 golden vectors pass with UTF-8 mode.
Earlier user verification: 29 tests passed. Direct localhost access is now working
for the agent. The auth slice full run passed 57 tests without skips, with 97%
backend line coverage (auth service 94%, auth API 100%), including two initialization
guard checks. One existing Starlette/AnyIO deprecation warning remains.
Ruff passes. Alembic has one head, 0002_authentication; application migration was
applied. Real PostgreSQL/Redis checks cover live API readiness, MFA concurrency,
code replay, audit, expiry, logout, scope denial, demo guard and migration round trip.
Final backend count is recorded in CHANGELOG. Frontend production compilation
(strict TypeScript + Vite) passed on Node 24.16.0; target remains Node 22.
Browser, axe, frontend tests and mypy checks are pending. Interactive user
provisioning was not exercised end to end.
On this managed workspace uv's default user cache was denied during a later run;
setting UV_CACHE_DIR to `.tmp/uv-cache` resolved it. Dependencies installed and
uv.lock exists. Commands and limitations are recorded in CHANGELOG.md.

## Next concrete task

User requested Shopify integration and versatility for five stores. First manual
multi-store slice is implemented; follow docs/runbooks/local-shopify.md to install
apps and configure secrets in a human terminal. Domains/ownership were not given.
Choose auth per store: same-organization client credentials or a provisioned
offline token. OAuth install UI/refresh, bulk worker, webhooks/HMAC, Payments,
normalization/refund/tax/fee reconciliation and profit reporting remain pending.
DISC-10/29 remain open; current implementation is not full WP-12 acceptance.

Complete the frontend login/browser/accessibility acceptance checks when requested,
then continue WP-03 invitations / scoped role management under users.manage, with
audit/demo protection, and WP-04 workspace directory/entity configuration. The
frontend currently labels workspaces with numbered IDs; wire real names when the
directory API exists. Then durable jobs/privacy and reporting ingestion/calculations.
Read docs/runbooks/local-frontend.md to start UI and API. Do not rebuild existing auth.

## Pending work and dependencies

- WP-01 human discovery/requirement freeze and connector access decisions.
- WP-03 invitations / role management, real email sender, AWS/Vault auth key
  adapters, remembered-device policy, worker/scheduler/queue dispatch and durable
  job processing, broader demo fixtures, telemetry/privacy jobs, mypy/CI gates.
- Password reset and self-service MFA enrollment remain pending; the
  backend requires MFA by default, with an explicitly enabled local password-only
  override; MFA secrets support local/test devfile keys only.
- React app and dashboard shell now exist. Workspace/entity directory, other provider
  connectors, ledger normalization, all business calculations and reporting APIs remain
  unimplemented. Chart/Map/P&L/Trends show explicit unavailable states, not mock data.
- Frontend browser/axe acceptance and full design-system rollout remain pending.
- Git repository now exists (initial commit fc7c69f); application work is untracked
  and the earlier prompts/AGENTS.md modification remains. No commits or pushes
  were made in this session. No CI, GitHub PR, AWS deployment or production resources.
- Docker PostgreSQL/Redis containers remain running; agent direct TCP access now
  works and was used for live checks. Docker pipe access was previously denied.
  Node installed here is 24.16.0; Node 22 is pinned in web/.nvmrc. Frontend
  dependencies are installed with a committed-ready package-lock.json.
- No live provider access, source fact verification or CA confirmation.

## Resume protocol

1. Read this file, ARCHITECTURE.md and the latest CHANGELOG.md entry.
2. Inspect current files and Git state if a repository has since been initialized.
3. Read only the next task's spec sections, register records and code.
4. Keep engineering inputs unchanged and omitted scope unimplemented.
5. Record actual commands/results and update status before ending the session.
