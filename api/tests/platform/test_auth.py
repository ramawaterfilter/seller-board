import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from app.main import create_app
from app.settings import Settings
from app.workspace.api.deps import require_permission
from app.workspace.service.auth import PASSWORDS
from app.workspace.service.auth_secrets import AuthSecrets
from app.workspace.service.session import token_hash
from app.workspace.service.totp import totp_code
from cryptography.fernet import Fernet
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

pytestmark = [pytest.mark.db, pytest.mark.req("REQ-001")]
PASSWORD = "synthetic-password-for-tests"
SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
ROOT = Path(__file__).resolve().parents[3]


class Mailbox:
    def __init__(self):
        self.messages = []

    async def send(self, recipient, code):
        self.messages.append((recipient, code))


@pytest.fixture(scope="module")
def auth_engine():
    url = os.environ.get("RCI_TEST_DATABASE_URL")
    if not url:
        pytest.skip("RCI_TEST_DATABASE_URL not configured; needs real PostgreSQL and Redis")
    parsed = make_url(url)
    assert parsed.host in {"localhost", "127.0.0.1"} and parsed.database.startswith("rci_test")
    engine = create_engine(url, hide_parameters=True)
    old = os.environ.get("RCI_DATABASE_URL")
    os.environ["RCI_DATABASE_URL"] = url
    try:
        command.upgrade(Config(str(ROOT / "api/alembic.ini")), "head")
        yield engine, url
    finally:
        if old is None:
            os.environ.pop("RCI_DATABASE_URL", None)
        else:
            os.environ["RCI_DATABASE_URL"] = old
        engine.dispose()


@pytest.fixture
def auth_client(auth_engine):
    engine, url = auth_engine
    user, workspace, other, role = (uuid4() for _ in range(4))
    email = f"{user}@example.test"
    store = AuthSecrets(Fernet.generate_key())
    mailbox = Mailbox()
    with engine.begin() as connection:
        connection.execute(
            text("INSERT INTO ws.workspace(id,name) VALUES (:id,'SYNTH')"),
            [{"id": workspace}, {"id": other}],
        )
        connection.execute(
            text(
                'INSERT INTO ws."user"(id,email,display_name,password_hash) '
                "VALUES (:id,:email,'SYNTH',:hash)"
            ),
            {"id": user, "email": email, "hash": PASSWORDS.hash(PASSWORD)},
        )
        connection.execute(
            text("INSERT INTO ws.role(id,workspace_id,name) VALUES (:id,:ws,'finance')"),
            {"id": role, "ws": workspace},
        )
        connection.execute(
            text("""
            INSERT INTO ws.permission_scope(workspace_id,user_id,role_id,function_code,
                                            product_scope,market_scope)
            VALUES (:ws,:user,:role,'profit.read','product:SYNTH','country:IN')
        """),
            {"ws": workspace, "user": user, "role": role},
        )
        connection.execute(
            text(
                "INSERT INTO ws.mfa_secret(user_id,method,secret_enc) VALUES (:user,'totp',:secret)"
            ),
            {"user": user, "secret": store.encrypt(SECRET)},
        )
    settings = Settings(
        _env_file=None,
        env="test",
        database_url=url,
        redis_url=os.environ.get("RCI_REDIS_URL", "redis://127.0.0.1:6379/0"),
    )
    app = create_app(settings)
    app.state.auth_secrets = store
    app.state.email_sender = mailbox

    @app.get("/test/profit/in")
    async def india(
        user=Depends(
            require_permission("profit.read", product="product:SYNTH", market="country:IN")
        ),
    ):
        return {"allowed": True}

    @app.get("/test/profit/uk")
    async def uk(
        user=Depends(
            require_permission("profit.read", product="product:SYNTH", market="country:UK")
        ),
    ):
        return {"allowed": True}

    @app.post("/test/write")
    async def write(
        user=Depends(
            require_permission("profit.read", product="product:SYNTH", market="country:IN")
        ),
    ):
        return {"allowed": True}

    with TestClient(app, client=(f"SYNTH-{user}", 50000)) as client:
        yield client, engine, user, email, workspace, other, mailbox


def login(client, email, method="totp", password=PASSWORD):
    return client.post(
        "/api/v1/auth/login", json={"email": email, "password": password, "method": method}
    )


def finish_login(client, email, method="totp", mailbox=None):
    challenge = login(client, email, method)
    assert challenge.status_code == 200, challenge.text
    code = (
        mailbox.messages[-1][1]
        if method == "email"
        else totp_code(SECRET, int(datetime.now(UTC).timestamp()) // 30)
    )
    verified = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": challenge.json()["challenge_id"], "code": code},
    )
    assert verified.status_code == 200, verified.text
    return verified


def test_totp_login_session_hash_and_audit(auth_client):
    client, engine, user, email, workspace, _, _ = auth_client
    assert client.get("/api/v1/me").status_code == 401
    pending = login(client, email)
    assert pending.status_code == 200
    assert "rci_session" not in client.cookies
    code = totp_code(SECRET, int(datetime.now(UTC).timestamp()) // 30)
    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": pending.json()["challenge_id"], "code": code},
    )
    assert response.status_code == 200, response.text
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert response.headers["cache-control"] == "no-store"
    token = client.cookies["rci_session"]
    assert token not in response.text
    identity = client.get("/api/v1/me").json()
    assert identity["id"] == str(user)
    assert identity["workspace_ids"] == [str(workspace)]
    with engine.connect() as connection:
        assert connection.execute(
            text("SELECT token_hash FROM ws.session WHERE user_id=:id"), {"id": user}
        ).scalar_one() == token_hash(token)
        logs = connection.execute(
            text("SELECT action,after FROM platform.audit_log WHERE actor_user_id=:id ORDER BY id"),
            {"id": user},
        ).all()
        assert logs[-1] == ("login.success", {"method": "totp"})
        assert PASSWORD not in str(logs) and SECRET not in str(logs)


def test_email_code_single_use_and_challenge_rotation(auth_client):
    client, _, _, email, _, _, mailbox = auth_client
    first = login(client, email, "email").json()
    first_code = mailbox.messages[-1][1]
    second = login(client, email, "email").json()
    second_code = mailbox.messages[-1][1]
    assert (
        client.post(
            "/api/v1/auth/mfa/verify",
            json={"challenge_id": first["challenge_id"], "code": first_code},
        ).status_code
        == 401
    )
    response = client.post(
        "/api/v1/auth/mfa/verify",
        json={"challenge_id": second["challenge_id"], "code": second_code},
    )
    assert response.status_code == 200
    assert (
        client.post(
            "/api/v1/auth/mfa/verify",
            json={"challenge_id": second["challenge_id"], "code": second_code},
        ).status_code
        == 401
    )


def test_bad_password_commits_failures_and_throttle(auth_client):
    client, engine, user, email, _, _, _ = auth_client
    for _ in range(5):
        response = login(client, email, password="incorrect")
        assert response.status_code == 401
    assert login(client, email).status_code == 429
    with engine.connect() as connection:
        state = connection.execute(
            text('SELECT failed_attempts,locked_until FROM ws."user" WHERE id=:id'), {"id": user}
        ).one()
        assert state.failed_attempts == 5 and state.locked_until > datetime.now(UTC)
        assert (
            connection.execute(
                text(
                    "SELECT count(*) FROM platform.audit_log "
                    "WHERE actor_user_id=:id AND action='login.failure'"
                ),
                {"id": user},
            ).scalar_one()
            == 5
        )


def test_wrong_mfa_cannot_reset_global_failures(auth_client):
    client, engine, user, email, _, _, mailbox = auth_client
    for attempt_count in (3, 2):
        challenge = login(client, email, "email").json()
        bad_code = "000000" if mailbox.messages[-1][1] != "000000" else "111111"
        for _ in range(attempt_count):
            assert (
                client.post(
                    "/api/v1/auth/mfa/verify",
                    json={"challenge_id": challenge["challenge_id"], "code": bad_code},
                ).status_code
                == 401
            )
    with engine.connect() as connection:
        state = connection.execute(
            text('SELECT failed_attempts,locked_until FROM ws."user" WHERE id=:id'), {"id": user}
        ).one()
        assert state.failed_attempts == 5 and state.locked_until > datetime.now(UTC)
    assert "rci_session" not in client.cookies


@pytest.mark.req("REQ-006")
@pytest.mark.req("REQ-007")
def test_scoped_permissions_and_demo_write_guard(auth_client):
    client, engine, _, email, workspace, other, _ = auth_client
    verified = finish_login(client, email)
    headers = {"X-Workspace-Id": str(workspace)}
    assert client.get("/api/v1/auth/permissions", headers=headers).status_code == 200
    assert (
        client.get("/api/v1/auth/permissions", headers={"X-Workspace-Id": str(other)}).status_code
        == 404
    )
    assert client.get("/test/profit/in", headers=headers).status_code == 200
    assert client.get("/test/profit/uk", headers=headers).status_code == 404
    assert client.post("/test/write", headers=headers).status_code == 403
    headers["X-CSRF-Token"] = verified.json()["csrf_token"]
    assert client.post("/test/write", headers=headers).status_code == 200
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE ws.workspace SET demo_mode=true WHERE id=:id"), {"id": workspace}
        )
    assert client.post("/test/write", headers=headers).json()["error"]["code"] == "DEMO_READ_ONLY"


def test_logout_csrf_and_revocation(auth_client):
    client, engine, user, email, _, _, _ = auth_client
    verified = finish_login(client, email)
    assert client.post("/api/v1/auth/logout").status_code == 403
    response = client.post(
        "/api/v1/auth/logout", headers={"X-CSRF-Token": verified.json()["csrf_token"]}
    )
    assert response.status_code == 204
    assert "rci_session" not in client.cookies
    assert client.get("/api/v1/me").status_code == 401
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT revoked_at FROM ws.session WHERE user_id=:id"), {"id": user}
            ).scalar_one()
            is not None
        )


@pytest.mark.parametrize(
    "change",
    ["expires_at=created_at+interval '1 millisecond'", "last_seen_at=now()-interval '13 hours'"],
)
def test_session_absolute_and_idle_expiry(auth_client, change):
    client, engine, user, email, _, _, _ = auth_client
    finish_login(client, email)
    with engine.begin() as connection:
        connection.execute(text(f"UPDATE ws.session SET {change} WHERE user_id=:id"), {"id": user})
    assert client.get("/api/v1/me").status_code == 401


def test_disabled_user_and_expired_membership(auth_client):
    client, engine, user, email, workspace, _, _ = auth_client
    finish_login(client, email)
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE ws.permission_scope SET expires_at=now()-interval '1 second' "
                "WHERE user_id=:id"
            ),
            {"id": user},
        )
    assert (
        client.get(
            "/api/v1/auth/permissions", headers={"X-Workspace-Id": str(workspace)}
        ).status_code
        == 404
    )
    with engine.begin() as connection:
        connection.execute(
            text("UPDATE ws.\"user\" SET status='disabled' WHERE id=:id"), {"id": user}
        )
    assert client.get("/api/v1/me").status_code == 401


def test_cross_origin_and_sensitive_validation(auth_client):
    client, _, _, email, _, _, _ = auth_client
    response = client.post(
        "/api/v1/auth/login",
        headers={"Origin": "https://untrusted.example.test"},
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 403
    response = client.post(
        "/api/v1/auth/mfa/verify", json={"challenge_id": str(uuid4()), "code": "synthetic-secret"}
    )
    assert response.status_code == 422
    assert "synthetic-secret" not in response.text


def test_concurrent_mfa_has_one_winner(auth_client):
    client, _, _, email, _, _, mailbox = auth_client
    challenge = login(client, email, "email").json()
    body = {"challenge_id": challenge["challenge_id"], "code": mailbox.messages[-1][1]}
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(lambda _: client.post("/api/v1/auth/mfa/verify", json=body), range(2))
        )
    assert sorted(response.status_code for response in responses) == [200, 401]


def test_new_login_rotates_existing_session(auth_client):
    client, engine, _, email, _, _, mailbox = auth_client
    finish_login(client, email)
    old_token = client.cookies["rci_session"]
    finish_login(client, email, method="email", mailbox=mailbox)
    assert client.cookies["rci_session"] != old_token
    with engine.connect() as connection:
        assert (
            connection.execute(
                text("SELECT revoked_at FROM ws.session WHERE token_hash=:hash"),
                {"hash": token_hash(old_token)},
            ).scalar_one()
            is not None
        )


def test_totp_step_cannot_be_reused_for_a_new_challenge(auth_client):
    client, _, _, email, _, _, _ = auth_client
    first = login(client, email).json()
    code = totp_code(SECRET, int(datetime.now(UTC).timestamp()) // 30)
    assert (
        client.post(
            "/api/v1/auth/mfa/verify", json={"challenge_id": first["challenge_id"], "code": code}
        ).status_code
        == 200
    )
    challenge = login(client, email).json()
    response = client.post(
        "/api/v1/auth/mfa/verify", json={"challenge_id": challenge["challenge_id"], "code": code}
    )
    assert response.status_code == 401


def test_challenge_expiry_and_lockout_recovery(auth_client):
    client, engine, user, email, _, _, mailbox = auth_client
    challenge = login(client, email, "email").json()
    with engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE ws.auth_challenge SET expires_at=now()-interval '1 second' "
                "WHERE user_id=:id"
            ),
            {"id": user},
        )
    assert (
        client.post(
            "/api/v1/auth/mfa/verify",
            json={"challenge_id": challenge["challenge_id"], "code": mailbox.messages[-1][1]},
        ).status_code
        == 401
    )
    with engine.begin() as connection:
        connection.execute(
            text(
                'UPDATE ws."user" SET failed_attempts=5, '
                "locked_until=now()-interval '1 second' WHERE id=:id"
            ),
            {"id": user},
        )
    finish_login(client, email, "email", mailbox)
    with engine.connect() as connection:
        assert (
            connection.execute(
                text('SELECT failed_attempts FROM ws."user" WHERE id=:id'), {"id": user}
            ).scalar_one()
            == 0
        )


def test_unconfigured_email_sender_and_secure_cookie(auth_client):
    from app.workspace.service.email_otp import NullEmailSender

    client, _, _, email, _, _, _ = auth_client
    client.app.state.email_sender = NullEmailSender()
    assert login(client, email, "email").status_code == 503
    client.app.state.settings.env = "stage"
    verified = finish_login(client, email)
    assert "Secure" in verified.headers["set-cookie"]


def test_secret_store_missing_and_unknown_identity(auth_client, tmp_path):
    client, _, _, _, _, _, _ = auth_client
    response = login(client, f"{uuid4()}@example.test", password="incorrect")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    client.app.state.auth_secrets = None
    client.app.state.settings.dev_secrets_file = tmp_path / "missing.json"
    response = login(client, f"{uuid4()}@example.test")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_SECRETS_UNAVAILABLE"


def test_live_database_and_redis_readiness(auth_client):
    client, _, _, _, _, _, _ = auth_client
    response = client.get("/api/v1/readyz")
    assert response.status_code == 200
    assert response.json()["dependencies"] == {"postgres": "ok", "redis": "ok"}
