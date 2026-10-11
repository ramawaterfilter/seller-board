# Local authentication

WP-03 slice, REQ-001 / REQ-006 / REQ-007 / REQ-160. Backend and local TOTP login UI
implemented. See [frontend setup](local-frontend.md) for browser access on port 5173.

## Initialize and start

From project root, with local PostgreSQL/Redis running:

```powershell
uv sync --locked
# Copy only if you have not already configured .env:
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
uv run alembic -c api/alembic.ini upgrade head
uv run python scripts/initialize_local_auth.py
uv run uvicorn app.main:app --app-dir api/src --host 127.0.0.1 --reload
```

The helper asks for a synthetic local password (at least 12 characters), creates
user.finance@example.test and a demo workspace with India profit read permission.
It preserves an existing user and creates no live provider connections. It only
accepts localhost database rci_local and local/devfile configuration.

It generates an encryption key in `.tmp/auth-secrets.json` and saves the authenticator
secret plus otpauth enrollment URI to `.tmp/local-totp-enrollment.txt`. Both are
git-ignored local files. Enroll that secret in your authenticator manually. Keep
the files private; do not paste them into chat or commit them. The server never
returns a TOTP secret or an email code from login endpoints.

The interactive helper has syntax and rejection-guard checks; login tests seed
their own synthetic users instead of exercising this helper end to end.

## Try through API documentation

Open http://127.0.0.1:8000/api/v1/docs:

1. POST `/api/v1/auth/login` with email `user.finance@example.test`, your chosen
   password, and method `totp`. Save the returned challenge_id.
2. POST `/api/v1/auth/mfa/verify` with that challenge_id and the current six-digit
   authenticator code. Success sets the HttpOnly session cookie and returns a
   CSRF token. The browser sends the cookie automatically to subsequent API calls.
3. GET `/api/v1/me` returns your identity, workspace_ids and CSRF token.
4. GET `/api/v1/auth/permissions` with one returned ID in `X-Workspace-Id` returns
   your active grants for that workspace. An inaccessible workspace returns 404.
5. POST `/api/v1/auth/logout` with the CSRF token in `X-CSRF-Token`. This revokes
   the database session and removes the cookie.

No remember-device bypass, password reset, invitation or MFA enrollment API is
implemented yet. MFA is required by default. The frontend supports authenticator login;
email OTP remains unavailable until real delivery is configured.

## Temporary password-only local login

At the user's request, the current local `.env` sets `RCI_LOCAL_PASSWORD_LOGIN=true`.
Restart the API and return to the email/password form; a valid password now signs
in directly. No authenticator code is required. Existing accounts/passwords remain.
This option is accepted only with `RCI_ENV=local`; dev/stage reject it at startup.
To restore MFA, set it to false and restart the API. Password-only sessions then
become invalid and users must complete MFA again. These sessions store a null MFA
verification timestamp, and audit records identify method `password_local`.

## Implemented rules

Passwords use [Argon2id via argon2-cffi](https://argon2-cffi.readthedocs.io/en/stable/howto.html).
Authenticator verification follows [RFC 6238](https://datatracker.ietf.org/doc/html/rfc6238)
with 30-second steps, six digits and drift of one step either way. Used TOTP steps
cannot be reused for a new login; row locks serialize concurrent verification.
Secrets are encrypted with [Fernet](https://cryptography.io/en/latest/fernet/).

Challenges expire after five minutes, are single use and superseded by new login
challenges. Email codes are random six-digit values stored as a keyed digest bound
to the challenge; tests use an in-memory mailbox. NullEmailSender returns 503
instead of pretending to deliver mail. Sender calls have a ten-second deadline;
no external mail service was configured or contacted.

Five failures across password/MFA attempts lock the account for 15 minutes.
Correct passwords alone do not reset MFA failures. Redis limits each account to
five login requests and each direct client address to 60 authentication requests
per 15-minute window. Unknown and known accounts share the same throttling rule.
Forwarded-IP headers are not trusted; proxy deployments need a reviewed configuration.

Session tokens are random opaque values; only SHA-256 digests are stored. Limits
are 12 hours idle / seven days absolute, with rotation after MFA and database
revocation on logout. Cookies are HttpOnly, SameSite=Lax, and Secure in dev/stage.
Authentication responses use Cache-Control: no-store. Origin checks and CSRF
verification protect browser mutations; error envelopes never echo input secrets.

Workspace membership is checked using the authenticated identity before opening
a workspace transaction. Product/market/function checks require matching active
grants; unauthorized resources return 404. Demo mutations using the permission
dependency return DEMO_READ_ONLY. Future business routes must use that dependency
and transactional audit; these helpers are not automatic middleware for future routes.

Auth audits carry action, actor, trace ID and method only. Failed counters and
audit records commit even when login is rejected. Global auth audit records remain
unreadable by app_rw; insertion allocates an ID from the sequence without RETURNING,
which would require SELECT under row security.

Only local/test devfile auth secrets are supported. Dev/stage AWS/Vault key adapters
and real email delivery remain pending; auth fails closed without those adapters.
No production credentials were used.

## Verification

57 tests pass without skips against local PostgreSQL/Redis; backend line coverage
is 97%, auth service 94%, API routes 100%. Ruff passes. Alembic has one head
(0002_authentication); test fixtures exercise data-preserving downgrade/re-upgrade.
The application database migration was applied. Tests also probe live readiness
and the 155 reference vectors.

Coverage includes threads and greenlets, following
[Coverage.py's concurrency configuration](https://coverage.readthedocs.io/en/latest/config.html#run-concurrency)
for SQLAlchemy async execution. Auth fixtures retain synthetic records in the
dedicated test database; each run uses unique identities.
