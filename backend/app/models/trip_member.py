import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

TRIP_MEMBER_ROLES = ("owner", "editor")


class TripMember(Base, TimestampMixin):
    __tablename__ = "trip_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False, server_default="editor")

    __table_args__ = (
        UniqueConstraint("trip_id", "user_id", name="trip_user"),
        CheckConstraint("role IN ('owner','editor')", name="role"),
        Index("ix_trip_members_user_id", "user_id"),
        Index("ix_trip_members_trip_id", "trip_id"),
    )
