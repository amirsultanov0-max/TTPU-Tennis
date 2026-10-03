"""add match result tracking

Revision ID: ae8ef7ca16e8
Revises: 6ae0d7ce3062
Create Date: 2026-10-02 23:30:44.547767

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision: str = "ae8ef7ca16e8"
down_revision: Union[str, Sequence[str], None] = "6ae0d7ce3062"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add result submission and confirmation tracking
    to the matches table.
    """

    op.add_column(
        "matches",
        sa.Column(
            "result_status",
            sa.String(length=30),
            nullable=False,
            server_default="not_submitted",
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "result_submitted_by_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "player_one_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "player_two_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "result_submitted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "result_confirmed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_match_result_submitted_by",
        "matches",
        "users",
        ["result_submitted_by_id"],
        ["id"],
    )

    op.create_index(
        "idx_match_result_status",
        "matches",
        ["result_status"],
        unique=False,
    )

    op.create_index(
        "idx_match_result_submitted_by",
        "matches",
        ["result_submitted_by_id"],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove result submission and confirmation tracking
    from the matches table.
    """

    op.drop_index(
        "idx_match_result_submitted_by",
        table_name="matches",
    )

    op.drop_index(
        "idx_match_result_status",
        table_name="matches",
    )

    op.drop_constraint(
        "fk_match_result_submitted_by",
        "matches",
        type_="foreignkey",
    )

    op.drop_column(
        "matches",
        "result_confirmed_at",
    )

    op.drop_column(
        "matches",
        "result_submitted_at",
    )

    op.drop_column(
        "matches",
        "player_two_score",
    )

    op.drop_column(
        "matches",
        "player_one_score",
    )

    op.drop_column(
        "matches",
        "result_submitted_by_id",
    )

    op.drop_column(
        "matches",
        "result_status",
    )