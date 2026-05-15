import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, SoftDeleteMixin, TimestampMixin

INSPIRATION_TYPES = ("short", "long")
INSPIRATION_STATUSES = ("idea", "planned")


class TravelInspiration(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "travel_inspirations"

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
    destination: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="idea"
    )

    __table_args__ = (
        CheckConstraint("type IN ('short','long')", name="type"),
        CheckConstraint("status IN ('idea','planned')", name="status"),
        Index("ix_travel_inspirations_user_status", "user_id", "status"),
        Index("ix_travel_inspirations_user_created", "user_id", "created_at"),
    )
