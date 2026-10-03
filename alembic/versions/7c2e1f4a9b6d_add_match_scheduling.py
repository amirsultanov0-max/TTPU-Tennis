"""add match scheduling

Revision ID: 7c2e1f4a9b6d
Revises: 32f3ae6a319c
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7c2e1f4a9b6d"
down_revision: Union[str, Sequence[str], None] = "32f3ae6a319c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add match scheduling support."""

    op.add_column(
        "matches",
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    op.create_table(
        "schedule_requests",

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "match_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "requested_by_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "recipient_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "proposed_at",
            sa.DateTime(timezone=True),
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
            ["match_id"],
            ["matches.id"],
            name="fk_schedule_request_match",
        ),

        sa.ForeignKeyConstraint(
            ["requested_by_id"],
            ["users.id"],
            name="fk_schedule_request_requested_by",
        ),

        sa.ForeignKeyConstraint(
            ["recipient_id"],
            ["users.id"],
            name="fk_schedule_request_recipient",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_schedule_request_match_status",
        "schedule_requests",
        ["match_id", "status"],
        unique=False,
    )

    op.create_index(
        "idx_schedule_request_recipient_status",
        "schedule_requests",
        ["recipient_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    """Remove match scheduling support."""

    op.drop_index(
        "idx_schedule_request_recipient_status",
        table_name="schedule_requests",
    )

    op.drop_index(
        "idx_schedule_request_match_status",
        table_name="schedule_requests",
    )

    op.drop_table("schedule_requests")

    op.drop_column(
        "matches",
        "scheduled_at",
    )