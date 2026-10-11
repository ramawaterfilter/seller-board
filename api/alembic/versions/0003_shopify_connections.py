"""Local CON-05 connection and raw ingestion foundation; additive downgrade."""

from pathlib import Path

from alembic import op

revision = "0003_shopify_connections"
down_revision = "0002_authentication"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    # Keep connector state and ingested evidence under the additive migration policy.
    pass
