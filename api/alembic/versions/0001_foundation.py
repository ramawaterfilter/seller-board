"""WP-03 platform persistence; REQ-001, REQ-006, REQ-160.

Downgrade preserves foundation data and protections under the additive-only policy.
Re-upgrade is idempotent. Destructive teardown is deliberately not a migration.
"""
from pathlib import Path

from alembic import op

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = Path(__file__).with_suffix(".sql").read_text(encoding="utf-8")
    op.execute(sql)


def downgrade() -> None:
    # Keep identity, durable jobs and audit history; only Alembic's revision is rolled back.
    pass
