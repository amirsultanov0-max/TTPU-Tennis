"""add result reminder tracking

Revision ID: 6ae0d7ce3062
Revises: 7c2e1f4a9b6d
Create Date: 2026-10-02 13:04:32.759779

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6ae0d7ce3062"
down_revision: Union[str, Sequence[str], None] = "7c2e1f4a9b6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add result reminder tracking to matches."""
    op.add_column(
        "matches",
        sa.Column(
            "result_reminder_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove result reminder tracking from matches."""
    op.drop_column(
        "matches",
        "result_reminder_sent_at",
    )