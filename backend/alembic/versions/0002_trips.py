"""create trips table

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trips",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=128), nullable=False),
        sa.Column("destination_city", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=16),
            server_default="draft",
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=512), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "timezone",
            sa.String(length=32),
            server_default="Asia/Shanghai",
            nullable=False,
        ),
        sa.Column(
            "created_via",
            sa.String(length=16),
            server_default="manual",
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
        sa.PrimaryKeyConstraint("id", name="pk_trips"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_trips_user_id_users",
        ),
        sa.CheckConstraint(
            "status IN ('draft','planning','confirmed','completed','archived')",
            name="status",
        ),
        sa.CheckConstraint(
            "created_via IN ('manual','ai_import')",
            name="created_via",
        ),
        sa.CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR start_date <= end_date",
            name="date_range",
        ),
    )
    op.create_index(
        "ix_trips_user_status_start",
        "trips",
        ["user_id", "status", "start_date"],
    )
    op.create_index(
        "ix_trips_user_deleted",
        "trips",
        ["user_id", "deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_trips_user_deleted", table_name="trips")
    op.drop_index("ix_trips_user_status_start", table_name="trips")
    op.drop_table("trips")
