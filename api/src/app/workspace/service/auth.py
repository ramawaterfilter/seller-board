import asyncio
import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.errors import AppError
from app.platform.audit import append_audit
from app.workspace.service.session import issue_session, token_hash
from app.workspace.service.totp import verify_totp
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from sqlalchemy import text

PASSWORDS = PasswordHasher()
DUMMY_HASH = PASSWORDS.hash(secrets.token_urlsafe(32))


def password_matches(hashed: str | None, password: str) -> bool:
    try:
        valid = PASSWORDS.verify(hashed or DUMMY_HASH, password)
        return valid and hashed is not None
    except (VerificationError, ValueError):
        return False


class LoginLimiter:
    def __init__(self, redis):
        self.redis = redis

    async def check(self, kind: str, value: str, limit: int) -> None:
        key = f"rci:auth:{kind}:{hashlib.sha256(value.encode()).hexdigest()}"
        try:
            count = await self.redis.eval(
                """
                local n=redis.call('INCR',KEYS[1])
                if n==1 then redis.call('EXPIRE',KEYS[1],900) end
                return n
            """,
                1,
                key,
            )
        except Exception:
            raise AppError(
                503, "AUTH_LIMITER_UNAVAILABLE", "Sign in is temporarily unavailable."
            ) from None
        if count > limit:
            raise AppError(429, "AUTH_COOLDOWN", "Too many attempts. Try again in 15 minutes.")


class AuthService:
    def __init__(self, database, auth_secrets, sender, *, password_only: bool = False):
        self.database, self.secrets, self.sender = database, auth_secrets, sender
        self.password_only = password_only

    async def record(self, session, action, trace_id, user_id=None, method=None):
        await append_audit(
            session,
            workspace_id=None,
            actor_user_id=user_id,
            action=action,
            trace_id=trace_id,
            after={"method": method} if method else None,
        )

    async def failed(self, session, user, now):
        await session.execute(
            text("""
            UPDATE ws."user" SET failed_attempts=failed_attempts+1,
              locked_until=CASE WHEN failed_attempts+1>=5 THEN :until ELSE locked_until END
            WHERE id=:id
        """),
            {"id": user["id"], "until": now + timedelta(minutes=15)},
        )

    async def login(
        self, email: str, password: str, method: str, trace_id: str, old_token: str | None = None
    ):
        now = datetime.now(UTC)
        async with self.database.sessions.begin() as session:
            result = await session.execute(
                text('SELECT * FROM ws."user" WHERE email=:email FOR UPDATE'), {"email": email}
            )
            user = result.mappings().one_or_none()
            valid = await asyncio.to_thread(
                password_matches, user["password_hash"] if user else None, password
            )
            if user and user["locked_until"] and user["locked_until"] <= now:
                await session.execute(
                    text('UPDATE ws."user" SET failed_attempts=0, locked_until=NULL WHERE id=:id'),
                    {"id": user["id"]},
                )
            locked = user and user["locked_until"] and user["locked_until"] > now
            if not valid or user is None or user["status"] != "active" or locked:
                if user and not locked:
                    await self.failed(session, user, now)
                await self.record(session, "login.failure", trace_id, user["id"] if user else None)
                # Return failure until after transaction commit: counters and audit must persist.
                return AppError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
            if self.password_only:
                if PASSWORDS.check_needs_rehash(user["password_hash"]):
                    hashed = await asyncio.to_thread(PASSWORDS.hash, password)
                    await session.execute(
                        text('UPDATE ws."user" SET password_hash=:hash WHERE id=:id'),
                        {"hash": hashed, "id": user["id"]},
                    )
                await session.execute(
                    text('UPDATE ws."user" SET failed_attempts=0, locked_until=NULL WHERE id=:id'),
                    {"id": user["id"]},
                )
                await session.execute(
                    text(
                        "UPDATE ws.auth_challenge SET consumed_at=:now "
                        "WHERE user_id=:user AND consumed_at IS NULL"
                    ),
                    {"now": now, "user": user["id"]},
                )
                if old_token:
                    await session.execute(
                        text("UPDATE ws.session SET revoked_at=:now WHERE token_hash=:h"),
                        {"now": now, "h": token_hash(old_token)},
                    )
                token = await issue_session(session, user["id"], now, mfa_verified=False)
                await self.record(session, "login.success", trace_id, user["id"], "password_local")
                return token
            if method == "totp":
                secret = (
                    await session.execute(
                        text("""
                    SELECT id FROM ws.mfa_secret WHERE user_id=:user AND method='totp'
                      AND consumed_at IS NULL
                """),
                        {"user": user["id"]},
                    )
                ).scalar_one_or_none()
                if secret is None:
                    return AppError(403, "MFA_NOT_ENROLLED", "Authenticator is not enrolled.")
            elif not user["mfa_email_enabled"]:
                return AppError(403, "MFA_NOT_ENROLLED", "Email verification is not enabled.")
            await session.execute(
                text(
                    "UPDATE ws.auth_challenge SET consumed_at=:now "
                    "WHERE user_id=:user AND consumed_at IS NULL"
                ),
                {"now": now, "user": user["id"]},
            )
            challenge = uuid4()
            code = f"{secrets.randbelow(1000000):06d}" if method == "email" else None
            await session.execute(
                text("""
                INSERT INTO ws.auth_challenge(id,user_id,method,code_hash,expires_at)
                VALUES (:id,:user,:method,:hash,:expires)
            """),
                {
                    "id": challenge,
                    "user": user["id"],
                    "method": method,
                    "hash": self.secrets.otp_digest(challenge, code) if code else None,
                    "expires": now + timedelta(minutes=5),
                },
            )
            if code:
                try:
                    async with asyncio.timeout(10):
                        await self.sender.send(user["email"], code)
                except Exception:
                    await session.execute(
                        text("UPDATE ws.auth_challenge SET consumed_at=:now WHERE id=:id"),
                        {"id": challenge, "now": now},
                    )
                    await self.record(session, "login.delivery_failure", trace_id, user["id"])
                    return AppError(
                        503,
                        "OTP_DELIVERY_UNAVAILABLE",
                        "Email code delivery is not configured or unavailable.",
                    )
            if PASSWORDS.check_needs_rehash(user["password_hash"]):
                hashed = await asyncio.to_thread(PASSWORDS.hash, password)
                await session.execute(
                    text('UPDATE ws."user" SET password_hash=:hash WHERE id=:id'),
                    {"hash": hashed, "id": user["id"]},
                )
            await self.record(session, "login.mfa_required", trace_id, user["id"], method)
            return {"challenge_id": str(challenge), "method": method, "expires_in": 300}

    async def verify(self, challenge_id: UUID, code: str, trace_id: str, old_token: str | None):
        now = datetime.now(UTC)
        error = AppError(401, "INVALID_MFA_CODE", "Verification code is invalid or expired.")
        async with self.database.sessions.begin() as session:
            user_id = (
                await session.execute(
                    text("SELECT user_id FROM ws.auth_challenge WHERE id=:id"), {"id": challenge_id}
                )
            ).scalar_one_or_none()
            if user_id is None:
                await self.record(session, "login.mfa_failure", trace_id)
                return error
            user = (
                (
                    await session.execute(
                        text('SELECT * FROM ws."user" WHERE id=:id FOR UPDATE'), {"id": user_id}
                    )
                )
                .mappings()
                .one()
            )
            challenge = (
                (
                    await session.execute(
                        text("SELECT * FROM ws.auth_challenge WHERE id=:id FOR UPDATE"),
                        {"id": challenge_id},
                    )
                )
                .mappings()
                .one()
            )
            if (
                user["status"] != "active"
                or challenge["consumed_at"] is not None
                or challenge["expires_at"] <= now
                or challenge["attempts"] >= 5
                or (user["locked_until"] is not None and user["locked_until"] > now)
            ):
                await self.record(session, "login.mfa_failure", trace_id, user_id)
                return error
            if user["locked_until"] and user["locked_until"] <= now:
                await session.execute(
                    text('UPDATE ws."user" SET failed_attempts=0, locked_until=NULL WHERE id=:id'),
                    {"id": user_id},
                )
            step = None
            if challenge["method"] == "email":
                valid = hmac.compare_digest(
                    self.secrets.otp_digest(challenge_id, code), challenge["code_hash"]
                )
            else:
                enrolled = (
                    (
                        await session.execute(
                            text("""
                    SELECT * FROM ws.mfa_secret WHERE user_id=:id AND method='totp'
                      AND consumed_at IS NULL FOR UPDATE
                """),
                            {"id": user_id},
                        )
                    )
                    .mappings()
                    .one_or_none()
                )
                if enrolled:
                    step = verify_totp(
                        self.secrets.decrypt(bytes(enrolled["secret_enc"])),
                        code,
                        int(now.timestamp()),
                        enrolled["last_verified_step"],
                    )
                valid = step is not None
            if not valid:
                await session.execute(
                    text("UPDATE ws.auth_challenge SET attempts=attempts+1 WHERE id=:id"),
                    {"id": challenge_id},
                )
                await self.failed(session, user, now)
                await self.record(
                    session, "login.mfa_failure", trace_id, user_id, challenge["method"]
                )
                return error
            if step is not None:
                await session.execute(
                    text("UPDATE ws.mfa_secret SET last_verified_step=:step WHERE id=:id"),
                    {"step": step, "id": enrolled["id"]},
                )
            await session.execute(
                text("UPDATE ws.auth_challenge SET consumed_at=:now WHERE id=:id"),
                {"now": now, "id": challenge_id},
            )
            await session.execute(
                text('UPDATE ws."user" SET failed_attempts=0,locked_until=NULL WHERE id=:id'),
                {"id": user_id},
            )
            if old_token:
                await session.execute(
                    text("UPDATE ws.session SET revoked_at=:now WHERE token_hash=:h"),
                    {"now": now, "h": token_hash(old_token)},
                )
            token = await issue_session(session, user_id, now)
            await self.record(session, "login.success", trace_id, user_id, challenge["method"])
            return token
