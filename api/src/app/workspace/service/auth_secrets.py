import hashlib
import hmac
import json

from app.errors import AppError
from app.settings import Settings
from cryptography.fernet import Fernet


class AuthSecrets:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
        self.key = key

    def encrypt(self, secret: str) -> bytes:
        return self.cipher.encrypt(secret.encode("ascii"))

    def decrypt(self, value: bytes) -> str:
        return self.cipher.decrypt(value).decode("ascii")

    def otp_digest(self, challenge_id, code: str) -> str:
        return hmac.new(
            self.key, f"email-otp:{challenge_id}:{code}".encode(), hashlib.sha256
        ).hexdigest()


def load_auth_secrets(settings: Settings) -> AuthSecrets:
    if settings.env not in {"local", "test"} or settings.secrets_backend != "devfile":
        raise AppError(
            503, "AUTH_SECRETS_UNAVAILABLE", "Authentication secrets are not configured."
        )
    try:
        data = json.loads(settings.dev_secrets_file.read_text(encoding="utf-8"))
        return AuthSecrets(data["auth_encryption_key"].encode("ascii"))
    except (OSError, ValueError, KeyError, TypeError):
        raise AppError(
            503,
            "AUTH_SECRETS_UNAVAILABLE",
            "Initialize the local authentication secrets before logging in.",
        ) from None
