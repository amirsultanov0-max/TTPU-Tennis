"""add loser_id to matches

Revision ID: b8ef203d3a04
Revises: 11e9bc979d10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8ef203d3a04"

down_revision: Union[str, Sequence[str], None] = "11e9bc979d10"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "matches",
        sa.Column(
            "loser_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_matches_loser_id_users",
        "matches",
        "users",
        ["loser_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_matches_loser_id_users",
        "matches",
        type_="foreignkey",
    )

    op.drop_column(
        "matches",
        "loser_id",
    )
