"""replace rating with ranking points

Revision ID: 970ab25737ad

Revises: 35c448fa92cc

Create Date: 2026-10-01 01:26:05.427508
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "970ab25737ad"

down_revision: Union[str, Sequence[str], None] = "35c448fa92cc"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "ranking_points",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.drop_column(
        "users",
        "rating",
    )

    op.alter_column(
        "users",
        "ranking_points",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "rating",
            sa.Integer(),
            nullable=False,
            server_default="1000",
        ),
    )

    op.drop_column(
        "users",
        "ranking_points",
    )

    op.alter_column(
        "users",
        "rating",
        server_default=None,
    )