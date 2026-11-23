"""alter_vector_dimensions_to_3072

Revision ID: e46bf1cf0fd7
Revises: 2c68fbd0a2f7
Create Date: 2026-09-01 20:50:15.481712

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "e46bf1cf0fd7"
down_revision: str | Sequence[str] | None = "2c68fbd0a2f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""


def downgrade() -> None:
    """Downgrade schema."""
