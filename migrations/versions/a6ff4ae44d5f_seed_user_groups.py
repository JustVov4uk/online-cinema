"""seed user groups

Revision ID: a6ff4ae44d5f
Revises: 04da5425d2f5
Create Date: 2026-07-05 16:07:34.390877

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a6ff4ae44d5f"
down_revision: str | Sequence[str] | None = "04da5425d2f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # noinspection SqlResolve
    op.execute(
        """
        INSERT INTO user_groups (name)
        VALUES ('USER'), ('MODERATOR'), ('ADMIN')
        ON CONFLICT (name) DO NOTHING
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    # noinspection SqlResolve
    op.execute(
        """
        DELETE FROM user_groups
        WHERE name IN ('USER', 'MODERATOR', 'ADMIN')
        """
    )
