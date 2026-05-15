"""add coordinates to trip_events

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-15

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("trip_events", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("trip_events", sa.Column("longitude", sa.Float(), nullable=True))
    op.create_check_constraint(
        "ck_trip_events_coordinate_pair",
        "trip_events",
        "(latitude IS NULL AND longitude IS NULL) OR "
        "(latitude IS NOT NULL AND longitude IS NOT NULL)",
    )
    op.create_check_constraint(
        "ck_trip_events_latitude_range",
        "trip_events",
        "latitude IS NULL OR (latitude >= -90 AND latitude <= 90)",
    )
    op.create_check_constraint(
        "ck_trip_events_longitude_range",
        "trip_events",
        "longitude IS NULL OR (longitude >= -180 AND longitude <= 180)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_trip_events_longitude_range",
        "trip_events",
        type_="check",
    )
    op.drop_constraint(
        "ck_trip_events_latitude_range",
        "trip_events",
        type_="check",
    )
    op.drop_constraint(
        "ck_trip_events_coordinate_pair",
        "trip_events",
        type_="check",
    )
    op.drop_column("trip_events", "longitude")
    op.drop_column("trip_events", "latitude")
