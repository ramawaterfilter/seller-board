import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from app.errors import AppError
from app.settings import Settings
from app.workspace.service.auth import PASSWORDS, LoginLimiter, password_matches
from app.workspace.service.auth_secrets import AuthSecrets, load_auth_secrets
from app.workspace.service.totp import totp_code, verify_totp
from cryptography.fernet import Fernet, InvalidToken

RFC_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
pytestmark = pytest.mark.req("REQ-001")


@pytest.mark.parametrize(
    "timestamp,expected",
    [
        (59, "94287082"),
        (1111111109, "07081804"),
        (1111111111, "14050471"),
        (2000000000, "69279037"),
    ],
)
def test_rfc6238_sha1_vectors(timestamp, expected):
    assert totp_code(RFC_SECRET, timestamp // 30, digits=8) == expected


def test_totp_drift_and_replay():
    code = totp_code(RFC_SECRET, 100)
    assert verify_totp(RFC_SECRET, code, 101 * 30, None) == 100
    assert verify_totp(RFC_SECRET, code, 102 * 30, None) is None
    assert verify_totp(RFC_SECRET, code, 100 * 30, 100) is None


def test_password_hashing_and_invalid_credentials():
    hashed = PASSWORDS.hash("synthetic-password-for-tests")
    assert hashed.startswith("$argon2id$")
    assert password_matches(hashed, "synthetic-password-for-tests")
    assert not password_matches(hashed, "incorrect")
    assert not password_matches(None, "incorrect")
    assert not password_matches("invalid-hash", "incorrect")


def test_encryption_and_keyed_email_digest():
    store = AuthSecrets(Fernet.generate_key())
    encrypted = store.encrypt(RFC_SECRET)
    assert RFC_SECRET.encode() not in encrypted
    assert store.decrypt(encrypted) == RFC_SECRET
    with pytest.raises(InvalidToken):
        store.decrypt(encrypted[:-2] + b"xx")
    assert store.otp_digest("one", "123456") != store.otp_digest("two", "123456")


def test_devfile_load_and_missing_key(tmp_path):
    path = tmp_path / "secrets.json"
    settings = Settings(_env_file=None, env="test", dev_secrets_file=path)
    with pytest.raises(AppError) as error:
        load_auth_secrets(settings)
    assert error.value.code == "AUTH_SECRETS_UNAVAILABLE"
    path.write_text(json.dumps({"auth_encryption_key": Fernet.generate_key().decode()}))
    assert isinstance(load_auth_secrets(settings), AuthSecrets)


def test_limiter_fails_closed_and_caps_attempts():
    redis = AsyncMock()
    redis.eval.return_value = 6
    with pytest.raises(AppError) as error:
        asyncio.run(LoginLimiter(redis).check("account", "synthetic@example.test", 5))
    assert error.value.status == 429
    redis.eval.side_effect = RuntimeError("synthetic-secret")
    with pytest.raises(AppError) as error:
        asyncio.run(LoginLimiter(redis).check("account", "synthetic@example.test", 5))
    assert error.value.status == 503
    assert "synthetic-secret" not in str(error.value)
