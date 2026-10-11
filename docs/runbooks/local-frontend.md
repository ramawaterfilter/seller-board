# Local frontend

The React frontend includes password/TOTP login, session restoration, workspace
selection, permission details and a responsive profit dashboard shell. It starts
in dark mode; the theme toggle also supports light mode.

## Open the interface

From the project root, open a PowerShell terminal:

```powershell
cd web
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. Select **Preview the interface** to explore without
an account. Preview is disconnected: it grants no access and contains no business
data. Dashboard tabs, channel/period selection and the details drawer work;
financial values remain missing. Unbuilt navigation modules are labelled Soon.

Node 22 is the target (`web/.nvmrc`). The current build also compiled on the installed
Node 24.16.0. Versions are pinned in package.json and package-lock.json.

## Sign in with the local API

Temporary local override requested by the user: `.env` now has
`RCI_LOCAL_PASSWORD_LOGIN=true`. With this flag and RCI_ENV=local, sign in using
email/password only. Restart the API after changing it. Authenticator enrollment
is needed only when MFA is enabled. The tracked example defaults to MFA enabled.

Keep PostgreSQL/Redis running. In a second terminal, from the project root:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
$env:UV_CACHE_DIR = Join-Path (Get-Location) '.tmp/uv-cache'
uv sync --locked
uv run alembic -c api/alembic.ini upgrade head
# First-time setup only: prompts for a local password and enrolls a synthetic user.
uv run python scripts/initialize_local_auth.py
uv run uvicorn app.main:app --app-dir api/src --host 127.0.0.1 --reload
```

Follow [local authentication](local-authentication.md) to enroll the generated TOTP
secret in an authenticator. Sign in at port 5173 with `user.finance@example.test`,
the password you chose, and a current six-digit authenticator code. Existing
accounts do not need initialization again. No default password is provided.

After MFA, choose an assigned workspace. Settings shows the active permission
scopes returned by the API. Profit requires a profit.read grant; the API remains
the authority for resource access. Workspace labels currently use numbered IDs
because the workspace directory API is not built.

The Vite development server proxies /api to port 8000. Use **127.0.0.1** consistently
in both browser URLs and RCI_WEB_ORIGIN; the default origin is
http://127.0.0.1:5173. Vite uses a strict port so it cannot silently move to a port
the API rejects. No broad CORS permission was added.

Cookies are HttpOnly. Identity, challenges, workspace selection and CSRF tokens
stay in memory. Only a non-sensitive theme preference is stored in localStorage.
Logout calls the API with CSRF verification; network failure keeps the session
visible and offers an error instead of pretending logout succeeded.

## Build

```powershell
cd web
npm run build
```

The build compiles strict TypeScript and creates web/dist. A deployed SPA will
need same-origin /api routing, SPA fallback, and no-store auth responses; the Vite
proxy is development-only. No deployment was performed.

## Current limits

This is a frontend foundation, not completed reporting. No provider connections,
profit calculations, charts, maps, exports, workspace directory, invitations,
password reset or self-service MFA enrollment exist yet. Email OTP is not offered
because a delivery provider is not configured. Missing amounts are not zero.

The production build passed. Browser journeys, mobile rendering and automated
axe accessibility checks were not run in this session; they remain required
before UI acceptance. No test suite was added or run for this slice.
