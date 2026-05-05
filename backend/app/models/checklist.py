import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin

CHECKLIST_CATEGORIES = (
    "document",
    "electronics",
    "clothing",
    "medicine",
    "food",
    "home",
    "pet",
    "task",
    "other",
)
CHECKLIST_SOURCES = ("template", "manual", "ai_generated")
_CATEGORY_CHECK = (
    "category IN ('document','electronics','clothing','medicine',"
    "'food','home','pet','task','other')"
)


class ChecklistTemplate(Base, TimestampMixin):
    """全局种子，无 user_id"""

    __tablename__ = "checklist_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    label: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    __table_args__ = (
        CheckConstraint(_CATEGORY_CHECK, name="category"),
    )


class ChecklistItem(Base, TimestampMixin):
    """用户每 trip 的清单实例（不软删，硬删）"""

    __tablename__ = "checklist_items"

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
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    checked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    category: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="other"
    )
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="manual"
    )
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("checklist_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )

    __table_args__ = (
        UniqueConstraint("trip_id", "label", name="trip_label"),
        CheckConstraint(_CATEGORY_CHECK, name="category"),
        CheckConstraint(
            "source IN ('template','manual','ai_generated')",
            name="source",
        ),
        Index(
            "ix_checklist_items_user_trip_sort",
            "user_id",
            "trip_id",
            "sort_order",
        ),
    )
