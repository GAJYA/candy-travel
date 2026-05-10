"""add canceled trip status

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-10

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("status", "trips", type_="check")
    op.create_check_constraint(
        "status",
        "trips",
        "status IN ('draft','planning','confirmed','completed','canceled','archived')",
    )


def downgrade() -> None:
    op.execute("UPDATE trips SET status = 'archived' WHERE status = 'canceled'")
    op.drop_constraint("status", "trips", type_="check")
    op.create_check_constraint(
        "status",
        "trips",
        "status IN ('draft','planning','confirmed','completed','archived')",
    )
