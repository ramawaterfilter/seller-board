"""Create a separate local integration workspace; preserve the read-only demo."""

import argparse
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api" / "src"))

from app.settings import Settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def main():
    parser = argparse.ArgumentParser(description="Create a local Shopify integration workspace.")
    parser.add_argument("--email", default="user.finance@example.test")
    args = parser.parse_args()
    settings = Settings()
    url = make_url(settings.database_url.get_secret_value()) if settings.database_url else None
    if (
        settings.env != "local"
        or not url
        or url.host not in {"localhost", "127.0.0.1"}
        or url.database != "rci_local"
        or not args.email.endswith("@example.test")
    ):
        raise SystemExit("Use a synthetic local user and localhost rci_local only.")
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT pg_advisory_xact_lock(hashtext('local-shopify-workspace'))"))
            user = conn.execute(
                text("SELECT id FROM ws.\"user\" WHERE email=:email AND status='active'"),
                {"email": args.email},
            ).scalar_one_or_none()
            if user is None:
                raise SystemExit("Initialize the local login account first.")
            workspace = conn.execute(
                text("""SELECT w.id FROM ws.workspace w JOIN ws.permission_scope p
              ON p.workspace_id=w.id WHERE w.name='Local Shopify integrations' AND w.demo_mode=false
              AND p.user_id=:user AND p.function_code='connectors.manage' LIMIT 1"""),
                {"user": user},
            ).scalar_one_or_none()
            if workspace is None:
                workspace, role = uuid4(), uuid4()
                conn.execute(
                    text(
                        "INSERT INTO ws.workspace(id,name,demo_mode) "
                        "VALUES (:id,'Local Shopify integrations',false)"
                    ),
                    {"id": workspace},
                )
                conn.execute(
                    text(
                        "INSERT INTO ws.role(id,workspace_id,name) "
                        "VALUES (:id,:ws,'Local integration administrator')"
                    ),
                    {"id": role, "ws": workspace},
                )
                for function in ("connectors.manage", "profit.read"):
                    conn.execute(
                        text("""INSERT INTO ws.permission_scope(workspace_id,user_id,role_id,
                      function_code,product_scope,market_scope)
                      VALUES (:ws,:user,:role,:function,'*','*')"""),
                        {"ws": workspace, "user": user, "role": role, "function": function},
                    )
                conn.execute(
                    text("""INSERT INTO platform.audit_log(workspace_id,actor_user_id,
                  actor_kind,action,trace_id)
                  VALUES (:ws,:user,'user','local.integration_workspace_created',:trace)"""),
                    {"ws": workspace, "user": user, "trace": str(uuid4())},
                )
        print(f"Integration workspace: {workspace}")
        print("Refresh the frontend and choose this workspace ID, then open Channels.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
