import json
from pathlib import Path
from uuid import UUID

from app.errors import AppError
from cryptography.fernet import Fernet, InvalidToken


def credential_paths(connector_id: UUID):
    root = Path(".tmp/connector-secrets").resolve()
    return root, root / "key", root / f"{connector_id}.enc"


def load_credentials(settings, connector: dict) -> dict:
    if settings.env != "local" or settings.secrets_backend != "devfile":
        raise AppError(
            503,
            "CONNECTOR_SECRETS_UNAVAILABLE",
            "Connector secret adapters are currently local-only.",
        )
    connector_id = UUID(str(connector["id"]))
    if connector["credential_ref"] != f"devfile:shopify/{connector_id}":
        raise AppError(
            503, "CONNECTOR_SECRETS_UNAVAILABLE", "Connector secret reference is invalid."
        )
    _, key, path = credential_paths(connector_id)
    try:
        data = json.loads(Fernet(key.read_bytes()).decrypt(path.read_bytes()))
        if (
            data["workspace_id"] != str(connector["workspace_id"])
            or data["shop_domain"] != connector["config"]["shop_domain"]
            or data["auth_mode"] != connector["config"]["auth_mode"]
        ):
            raise ValueError("binding mismatch")
        fields = (
            ("client_id", "client_secret")
            if data["auth_mode"] == "client_credentials"
            else ("access_token",)
        )
        if any(not isinstance(data.get(f), str) or not data[f] for f in fields):
            raise ValueError("missing credentials")
        return data
    except (OSError, ValueError, TypeError, KeyError, InvalidToken):
        raise AppError(
            503,
            "CONNECTOR_SECRETS_UNAVAILABLE",
            "Run the local Shopify credential setup command for this connection.",
        ) from None


def remove_credentials(settings, connector_id: UUID):
    if settings.env != "local" or settings.secrets_backend != "devfile":
        raise AppError(
            503,
            "CONNECTOR_SECRETS_UNAVAILABLE",
            "Connector secret adapters are currently local-only.",
        )
    root, _, target = credential_paths(connector_id)
    if target.parent != root:
        raise AppError(503, "CONNECTOR_SECRETS_UNAVAILABLE", "Invalid credential file location.")
    try:
        target.unlink(missing_ok=True)
    except OSError:
        raise AppError(
            503, "CONNECTOR_SECRETS_UNAVAILABLE", "Local credentials could not be removed."
        ) from None
