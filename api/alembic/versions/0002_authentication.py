"""WP-03 authentication state, REQ-001 and REQ-006. Data-preserving downgrade."""
from pathlib import Path

from alembic import op

revision = "0002_authentication"
down_revision = "0001_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(Path(__file__).with_suffix(".sql").read_text(encoding="utf-8"))


def downgrade() -> None:
    # Retain identity state, sessions and protections under the additive migration policy.
    pass
