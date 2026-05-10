"""create trip_members table

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trip_members",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=16), server_default="editor", nullable=False),
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
        sa.PrimaryKeyConstraint("id", name="pk_trip_members"),
        sa.UniqueConstraint("trip_id", "user_id", name="uq_trip_members_trip_id"),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            ondelete="CASCADE",
            name="fk_trip_members_trip_id_trips",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_trip_members_user_id_users",
        ),
        sa.CheckConstraint("role IN ('owner','editor')", name="role"),
    )
    op.create_index("ix_trip_members_user_id", "trip_members", ["user_id"])
    op.create_index("ix_trip_members_trip_id", "trip_members", ["trip_id"])
    op.execute(
        """
        INSERT INTO trip_members (trip_id, user_id, role)
        SELECT id, user_id, 'owner'
        FROM trips
        ON CONFLICT (trip_id, user_id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_trip_members_trip_id", table_name="trip_members")
    op.drop_index("ix_trip_members_user_id", table_name="trip_members")
    op.drop_table("trip_members")
