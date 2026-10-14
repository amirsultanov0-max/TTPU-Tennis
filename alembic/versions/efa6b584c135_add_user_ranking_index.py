"""add user ranking index

Revision ID: efa6b584c135
Revises: 25309394319b
Create Date: 2026-10-13 15:06:04.736187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efa6b584c135'
down_revision: Union[str, Sequence[str], None] = '25309394319b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the descending user ranking index."""
    op.execute(
        "CREATE INDEX idx_user_ranking "
        "ON users (ranking_points DESC)"
    )


def downgrade() -> None:
    """Remove the user ranking index."""
    op.execute("DROP INDEX idx_user_ranking")
