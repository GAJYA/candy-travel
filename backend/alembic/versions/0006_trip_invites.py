"""create trip_invites table

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trip_invites",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("inviter_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=96), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_trip_invites"),
        sa.UniqueConstraint("token", name="uq_trip_invites_token"),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            ondelete="CASCADE",
            name="fk_trip_invites_trip_id_trips",
        ),
        sa.ForeignKeyConstraint(
            ["inviter_user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_trip_invites_inviter_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["accepted_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
            name="fk_trip_invites_accepted_by_user_id_users",
        ),
    )
    op.create_index("ix_trip_invites_token", "trip_invites", ["token"])
    op.create_index("ix_trip_invites_trip_id", "trip_invites", ["trip_id"])
    op.create_index(
        "ix_trip_invites_inviter_user_id",
        "trip_invites",
        ["inviter_user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_trip_invites_inviter_user_id", table_name="trip_invites")
    op.drop_index("ix_trip_invites_trip_id", table_name="trip_invites")
    op.drop_index("ix_trip_invites_token", table_name="trip_invites")
    op.drop_table("trip_invites")
