import uuid
from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin

TRIP_STATUSES = ("draft", "planning", "confirmed", "completed", "archived")
TRIP_CREATED_VIA = ("manual", "ai_import")


class Trip(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "trips"

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
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    destination_city: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="draft"
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="Asia/Shanghai"
    )
    created_via: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="manual"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','planning','confirmed','completed','archived')",
            name="status",
        ),
        CheckConstraint(
            "created_via IN ('manual','ai_import')",
            name="created_via",
        ),
        CheckConstraint(
            "start_date IS NULL OR end_date IS NULL OR start_date <= end_date",
            name="date_range",
        ),
        Index("ix_trips_user_status_start", "user_id", "status", "start_date"),
        Index("ix_trips_user_deleted", "user_id", "deleted_at"),
    )
