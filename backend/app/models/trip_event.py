import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin

EVENT_TYPES = ("transport", "stay", "activity", "reminder")
EVENT_STATUSES = ("draft", "confirmed", "canceled")
EVENT_SOURCES = ("manual", "ai_extracted")


class TripEvent(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "trip_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    location_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    address: Mapped[str | None] = mapped_column(String(256), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="confirmed"
    )
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="manual"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('transport','stay','activity','reminder')",
            name="event_type",
        ),
        CheckConstraint(
            "status IN ('draft','confirmed','canceled')",
            name="status",
        ),
        CheckConstraint(
            "source IN ('manual','ai_extracted')",
            name="source",
        ),
        CheckConstraint(
            "end_at IS NULL OR end_at >= start_at",
            name="time_range",
        ),
        Index("ix_trip_events_user_trip_start", "user_id", "trip_id", "start_at"),
        Index(
            "ix_trip_events_user_trip_type_start",
            "user_id",
            "trip_id",
            "event_type",
            "start_at",
        ),
        Index("ix_trip_events_user_deleted", "user_id", "deleted_at"),
    )
