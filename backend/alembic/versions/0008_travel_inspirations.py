"""create travel_inspirations table

Revision ID: 0008
Revises: 0007
Create Date: 2026-05-14

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "travel_inspirations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("destination", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("plan_detail", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), server_default="idea", nullable=False),
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
        sa.CheckConstraint("type IN ('short','long')", name="ck_travel_inspirations_type"),
        sa.CheckConstraint(
            "status IN ('idea','planned')",
            name="ck_travel_inspirations_status",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_travel_inspirations_user_id_users",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_travel_inspirations"),
    )
    op.create_index(
        "ix_travel_inspirations_user_status",
        "travel_inspirations",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_travel_inspirations_user_created",
        "travel_inspirations",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_travel_inspirations_user_created", table_name="travel_inspirations"
    )
    op.drop_index(
        "ix_travel_inspirations_user_status", table_name="travel_inspirations"
    )
    op.drop_table("travel_inspirations")
