import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app.errors import AppError
from sqlalchemy import text


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def csrf_token(token: str) -> str:
    return hashlib.sha256(f"csrf:{token}".encode()).hexdigest()


async def issue_session(session, user_id, now: datetime, *, mfa_verified: bool = True) -> str:
    token = secrets.token_urlsafe(32)
    await session.execute(
        text("""
        INSERT INTO ws.session
          (user_id,token_hash,created_at,last_seen_at,expires_at,mfa_verified_at)
        VALUES (:user,:hash,:now,:now,:expires,:mfa_verified_at)
    """),
        {
            "user": user_id,
            "hash": token_hash(token),
            "now": now,
            "expires": now + timedelta(days=7),
            "mfa_verified_at": now if mfa_verified else None,
        },
    )
    return token


async def authenticated_user(database, token: str | None, *, allow_password_login: bool = False):
    if not token or len(token) > 256:
        raise AppError(401, "AUTH_REQUIRED", "Sign in to continue.")
    now = datetime.now(UTC)
    async with database.sessions.begin() as session:
        result = await session.execute(
            text("""
            SELECT u.id,u.email,u.display_name,
              CASE WHEN s.mfa_verified_at IS NULL THEN 'password' ELSE 'mfa' END
                AS authentication_method FROM ws.session s
            JOIN ws."user" u ON u.id=s.user_id
            WHERE s.token_hash=:hash AND s.revoked_at IS NULL AND u.status='active'
              AND (s.mfa_verified_at IS NOT NULL OR :allow_password) AND s.expires_at>:now
              AND s.last_seen_at>:idle_limit
            FOR UPDATE OF s
        """),
            {
                "hash": token_hash(token),
                "now": now,
                "idle_limit": now - timedelta(hours=12),
                "allow_password": allow_password_login,
            },
        )
        user = result.mappings().one_or_none()
        if user is not None:
            await session.execute(
                text("UPDATE ws.session SET last_seen_at=:now WHERE token_hash=:h"),
                {"now": now, "h": token_hash(token)},
            )
    if user is None:
        raise AppError(401, "AUTH_REQUIRED", "Sign in to continue.")
    return dict(user)
