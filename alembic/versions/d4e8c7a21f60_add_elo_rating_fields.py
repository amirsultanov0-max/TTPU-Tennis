"""Add precise Elo rating fields to users.

Revision ID: d4e8c7a21f60
Revises: c7a2d91e4b60
Create Date: 2026-10-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e8c7a21f60"
down_revision: Union[str, Sequence[str], None] = "c7a2d91e4b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "elo_rating",
            sa.Numeric(10, 6),
            nullable=False,
            server_default=sa.text("1000.000000"),
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "elo_matches_played",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "elo_matches_played")
    op.drop_column("users", "elo_rating")
