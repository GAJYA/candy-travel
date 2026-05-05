"""create checklist_templates + checklist_items tables and seed defaults

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-01

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_CATEGORY_CHECK = (
    "category IN ('document','electronics','clothing','medicine',"
    "'food','home','pet','task','other')"
)


def upgrade() -> None:
    # ---- checklist_templates ----
    op.create_table(
        "checklist_templates",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column(
            "sort_order", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "is_default",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
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
        sa.PrimaryKeyConstraint("id", name="pk_checklist_templates"),
        sa.UniqueConstraint("label", name="uq_checklist_templates_label"),
        sa.CheckConstraint(_CATEGORY_CHECK, name="category"),
    )

    # ---- checklist_items ----
    op.create_table(
        "checklist_items",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trip_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column(
            "checked",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(length=16),
            server_default="other",
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=16),
            server_default="manual",
            nullable=False,
        ),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "sort_order", sa.Integer(), server_default="0", nullable=False
        ),
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
        sa.PrimaryKeyConstraint("id", name="pk_checklist_items"),
        sa.UniqueConstraint("trip_id", "label", name="uq_checklist_items_trip_id"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
            name="fk_checklist_items_user_id_users",
        ),
        sa.ForeignKeyConstraint(
            ["trip_id"],
            ["trips.id"],
            ondelete="CASCADE",
            name="fk_checklist_items_trip_id_trips",
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["checklist_templates.id"],
            ondelete="SET NULL",
            name="fk_checklist_items_template_id_checklist_templates",
        ),
        sa.CheckConstraint(_CATEGORY_CHECK, name="category"),
        sa.CheckConstraint(
            "source IN ('template','manual','ai_generated')",
            name="source",
        ),
    )
    op.create_index(
        "ix_checklist_items_user_trip_sort",
        "checklist_items",
        ["user_id", "trip_id", "sort_order"],
    )

    # ---- 种子数据 ----
    seeds = [
        # (label, category, sort_order, is_default)
        ("护照", "document", 10, True),
        ("身份证", "document", 20, True),
        ("手机", "electronics", 10, True),
        ("充电器", "electronics", 20, True),
        ("充电宝", "electronics", 30, True),
        ("牙刷 / 牙膏", "other", 10, True),
        ("换洗衣物", "clothing", 10, True),
        ("常用药品", "medicine", 10, False),
        ("雨伞", "other", 20, False),
        ("防晒霜", "other", 30, False),
        ("锁好门", "home", 10, True),
        ("关煤气", "home", 20, True),
        ("拔掉不必要电器", "home", 30, False),
        ("关空调", "home", 40, False),
        ("喂宠物 / 加水", "pet", 10, False),
        ("清理猫砂", "pet", 20, False),
        ("给植物浇水", "pet", 30, False),
        ("设置邮件自动回复", "task", 10, False),
    ]
    op.bulk_insert(
        sa.table(
            "checklist_templates",
            sa.column("label", sa.String),
            sa.column("category", sa.String),
            sa.column("sort_order", sa.Integer),
            sa.column("is_default", sa.Boolean),
        ),
        [
            {
                "label": s[0],
                "category": s[1],
                "sort_order": s[2],
                "is_default": s[3],
            }
            for s in seeds
        ],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_checklist_items_user_trip_sort", table_name="checklist_items"
    )
    op.drop_table("checklist_items")
    op.drop_table("checklist_templates")
