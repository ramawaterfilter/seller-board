"""Initialize synthetic local TOTP login without printing credentials or secrets."""

import base64
import getpass
import json
import os
import secrets
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api/src"))

from app.settings import Settings
from app.workspace.service.auth_secrets import AuthSecrets
from argon2 import PasswordHasher
from cryptography.fernet import Fernet
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def main():
    settings = Settings()
    if settings.env != "local" or settings.secrets_backend != "devfile":
        raise SystemExit("This helper is for synthetic local development only.")
    if settings.database_url is None:
        raise SystemExit("Configure the local database URL first (see .env.example).")
    url = make_url(settings.database_url.get_secret_value())
    if url.host not in {"127.0.0.1", "localhost"} or url.database != "rci_local":
        raise SystemExit("Only the localhost rci_local database is allowed.")
    password = getpass.getpass("Choose a synthetic local password (at least 12 characters): ")
    if len(password) < 12 or len(password) > 1024:
        raise SystemExit("Password must contain 12 to 1024 characters.")
    if password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")
    target = settings.dev_secrets_file
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with target.open("x", encoding="utf-8") as output:
            json.dump({"auth_encryption_key": Fernet.generate_key().decode("ascii")}, output)
        os.chmod(target, 0o600)
    store = AuthSecrets(
        json.loads(target.read_text(encoding="utf-8"))["auth_encryption_key"].encode()
    )
    secret = base64.b32encode(secrets.token_bytes(20)).decode("ascii")
    workspace, user, role = (uuid4() for _ in range(3))
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.begin() as connection:
            exists = connection.execute(
                text('SELECT id FROM ws."user" WHERE email=:email'),
                {"email": "user.finance@example.test"},
            ).scalar_one_or_none()
            if exists:
                raise SystemExit(
                    "Synthetic user already exists; existing credentials were preserved."
                )
            connection.execute(
                text("INSERT INTO ws.workspace(id,name,demo_mode) VALUES (:id,'SYNTH Demo',true)"),
                {"id": workspace},
            )
            connection.execute(
                text(
                    'INSERT INTO ws."user"(id,email,display_name,password_hash) '
                    "VALUES (:id,'user.finance@example.test','SYNTH Finance',:hash)"
                ),
                {"id": user, "hash": PasswordHasher().hash(password)},
            )
            connection.execute(
                text(
                    "INSERT INTO ws.mfa_secret(user_id,method,secret_enc) "
                    "VALUES (:id,'totp',:secret)"
                ),
                {"id": user, "secret": store.encrypt(secret)},
            )
            connection.execute(
                text("INSERT INTO ws.role(id,workspace_id,name) VALUES (:id,:ws,'finance')"),
                {"id": role, "ws": workspace},
            )
            connection.execute(
                text("""
                INSERT INTO ws.permission_scope(workspace_id,user_id,role_id,function_code,
                                                product_scope,market_scope)
                VALUES (:ws,:user,:role,'profit.read','*','country:IN')
            """),
                {"ws": workspace, "user": user, "role": role},
            )
            enrollment = target.parent / "local-totp-enrollment.txt"
            with enrollment.open("x", encoding="utf-8") as output:
                output.write(f"Synthetic local authenticator secret: {secret}\n")
                output.write(
                    "otpauth://totp/RCI:user.finance%40example.test?"
                    f"secret={secret}&issuer=RCI&digits=6&period=30\n"
                )
            os.chmod(enrollment, 0o600)
    finally:
        engine.dispose()
    print("Synthetic local user created: user.finance@example.test")
    print(f"Authenticator enrollment is in {enrollment}. Keep this local file private.")


if __name__ == "__main__":
    main()
