"""create user groups table

Revision ID: 61a9fd5c5def
Revises:
Create Date: 2026-06-22 11:15:48.983664

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "61a9fd5c5def"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "name",
            sa.Enum("USER", "MODERATOR", "ADMIN", name="user_group_name"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_groups")
