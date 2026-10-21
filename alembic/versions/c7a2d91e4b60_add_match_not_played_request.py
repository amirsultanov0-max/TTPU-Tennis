"""add match not-played request tracking

Revision ID: c7a2d91e4b60
Revises: efa6b584c135
Create Date: 2026-10-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7a2d91e4b60"
down_revision: Union[str, Sequence[str], None] = "efa6b584c135"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add persistent tracking for match not-played requests."""
    op.add_column(
        "matches",
        sa.Column("not_played_requested_by_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column(
            "not_played_requested_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_match_not_played_requested_by",
        "matches",
        "users",
        ["not_played_requested_by_id"],
        ["id"],
    )


def downgrade() -> None:
    """Remove match not-played request tracking."""
    op.drop_constraint(
        "fk_match_not_played_requested_by",
        "matches",
        type_="foreignkey",
    )
    op.drop_column("matches", "not_played_requested_at")
    op.drop_column("matches", "not_played_requested_by_id")
