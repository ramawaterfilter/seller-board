"""Human-operated local credential enrollment. Never run with secrets in agent tasks."""

import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from uuid import UUID

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api" / "src"))

from app.ingestion.service.credentials import credential_paths
from app.settings import Settings
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def main():
    parser = argparse.ArgumentParser(description="Save encrypted backend-only Shopify credentials.")
    parser.add_argument("connector_id", type=UUID)
    args = parser.parse_args()
    settings = Settings()
    url = make_url(settings.database_url.get_secret_value()) if settings.database_url else None
    if (
        settings.env != "local"
        or settings.secrets_backend != "devfile"
        or not url
        or url.host not in {"localhost", "127.0.0.1"}
        or url.database != "rci_local"
    ):
        raise SystemExit("This helper only accepts local/devfile and localhost rci_local.")
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.connect() as conn:
            row = (
                conn.execute(
                    text("SELECT * FROM ing.connector WHERE id=:id"), {"id": args.connector_id}
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                raise SystemExit("Connection not found. Add the store in Channels first.")
            data = {
                "workspace_id": str(row["workspace_id"]),
                "shop_domain": row["config"]["shop_domain"],
                "auth_mode": row["config"]["auth_mode"],
            }
        print(f"Configure {data['shop_domain']} ({data['auth_mode']}).")
        root, key, target = credential_paths(args.connector_id)
        if target.exists() and input("Replace existing credentials? Type REPLACE: ") != "REPLACE":
            raise SystemExit("Existing credentials preserved.")
        if data["auth_mode"] == "client_credentials":
            if input("App and store belong to the same Shopify organization? Type YES: ") != "YES":
                raise SystemExit(
                    "Use merchant OAuth and an offline token for a different organization."
                )
            data["client_id"] = getpass.getpass("Shopify app client ID (hidden): ").strip()
            data["client_secret"] = getpass.getpass("Shopify app client secret (hidden): ").strip()
            if not data["client_id"] or not data["client_secret"]:
                raise SystemExit("Client ID and secret are required.")
        else:
            data["access_token"] = getpass.getpass(
                "Installed app's offline Admin API access token (hidden): "
            ).strip()
            if not data["access_token"]:
                raise SystemExit("An access token is required.")
        root.mkdir(parents=True, exist_ok=True)
        if not key.exists():
            with key.open("xb") as output:
                output.write(Fernet.generate_key())
            os.chmod(key, 0o600)
        encoded = Fernet(key.read_bytes()).encrypt(json.dumps(data).encode())
        temporary = root / f"{args.connector_id}.pending"
        with temporary.open("xb") as output:
            output.write(encoded)
        os.chmod(temporary, 0o600)
        temporary.replace(target)
        print("Encrypted credentials saved. Return to Channels and choose Verify connection.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
