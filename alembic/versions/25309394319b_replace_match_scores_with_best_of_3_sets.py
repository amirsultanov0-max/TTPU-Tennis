"""replace match scores with best of 3 sets

Revision ID: 25309394319b
Revises: ae8ef7ca16e8
Create Date: 2026-10-03 13:41:22.279663
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "25309394319b"
down_revision: Union[str, Sequence[str], None] = "ae8ef7ca16e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace match total scores with Best-of-3 set scores."""

    op.add_column(
        "matches",
        sa.Column(
            "set_1_player_one_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "set_1_player_two_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "set_2_player_one_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "set_2_player_two_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "set_3_player_one_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "matches",
        sa.Column(
            "set_3_player_two_score",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "idx_match_status",
        "matches",
        ["status"],
        unique=False,
    )

    op.drop_column(
        "matches",
        "player_two_score",
    )

    op.drop_column(
        "matches",
        "player_one_score",
    )


def downgrade() -> None:
    """Restore the previous match score columns."""

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

    op.drop_index(
        "idx_match_status",
        table_name="matches",
    )

    op.drop_column(
        "matches",
        "set_3_player_two_score",
    )

    op.drop_column(
        "matches",
        "set_3_player_one_score",
    )

    op.drop_column(
        "matches",
        "set_2_player_two_score",
    )

    op.drop_column(
        "matches",
        "set_2_player_one_score",
    )

    op.drop_column(
        "matches",
        "set_1_player_two_score",
    )

    op.drop_column(
        "matches",
        "set_1_player_one_score",
    )