"""create trip_events table

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trip_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location_name", sa.String(length=128), nullable=True),
        sa.Column("address", sa.String(length=256), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "meta",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default="confirmed",
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=16),
            server_default="manual",
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_trip_events"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_trip_events_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            ondelete="CASCADE",
            name="fk_trip_events_trip_id_trips",
        ),
        sa.CheckConstraint(
            "event_type IN ('transport','stay','activity','reminder')",
            name="event_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft','confirmed','canceled')",
            name="status",
        ),
        sa.CheckConstraint(
            "source IN ('manual','ai_extracted')",
            name="source",
        ),
        sa.CheckConstraint(
            "end_at IS NULL OR end_at >= start_at",
            name="time_range",
        ),
    )
    op.create_index(
        "ix_trip_events_user_trip_start",
        "trip_events",
        ["user_id", "trip_id", "start_at"],
    )
    op.create_index(
        "ix_trip_events_user_trip_type_start",
        "trip_events",
        ["user_id", "trip_id", "event_type", "start_at"],
    )
    op.create_index(
        "ix_trip_events_user_deleted",
        "trip_events",
        ["user_id", "deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_trip_events_user_deleted", table_name="trip_events")
    op.drop_index("ix_trip_events_user_trip_type_start", table_name="trip_events")
    op.drop_index("ix_trip_events_user_trip_start", table_name="trip_events")
    op.drop_table("trip_events")
