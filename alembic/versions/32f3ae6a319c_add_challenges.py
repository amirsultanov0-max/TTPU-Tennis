"""add challenges

Revision ID: 32f3ae6a319c
Revises: b8ef203d3a04
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "32f3ae6a319c"
down_revision: Union[str, Sequence[str], None] = "b8ef203d3a04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create challenges table."""

    op.create_table(
        "challenges",

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "challenger_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "opponent_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["challenger_id"],
            ["users.id"],
            name="fk_challenge_challenger",
        ),

        sa.ForeignKeyConstraint(
            ["opponent_id"],
            ["users.id"],
            name="fk_challenge_opponent",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_challenge_challenger_status",
        "challenges",
        ["challenger_id", "status"],
        unique=False,
    )

    op.create_index(
        "idx_challenge_opponent_status",
        "challenges",
        ["opponent_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    """Remove challenges table."""

    op.drop_index(
        "idx_challenge_opponent_status",
        table_name="challenges",
    )

    op.drop_index(
        "idx_challenge_challenger_status",
        table_name="challenges",
    )

    op.drop_table("challenges")
