from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ChecklistItem, ChecklistTemplate


async def copy_default_templates_to_trip(
    session: AsyncSession, *, user_id: UUID, trip_id: UUID
) -> int:
    """新建 trip 时调用：把 is_default=True 的模板拷贝到 checklist_items。

    必须在 trip 已经 flush（拿到 id）之后、commit 之前调用。
    返回拷贝的条数。
    """
    templates = await session.scalars(
        select(ChecklistTemplate)
        .where(ChecklistTemplate.is_default.is_(True))
        .order_by(ChecklistTemplate.category, ChecklistTemplate.sort_order)
    )
    count = 0
    for t in templates.all():
        session.add(
            ChecklistItem(
                user_id=user_id,
                trip_id=trip_id,
                label=t.label,
                category=t.category,
                sort_order=t.sort_order,
                source="template",
                template_id=t.id,
            )
        )
        count += 1
    return count
