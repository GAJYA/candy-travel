# F3-A — 行程详情后端（events + checklist + 摘要派生）

> 状态：设计中
> 依赖：F2 trips 基础 CRUD
> 后续：F3-B 前端 UI（用户单独提供 design.md 后开工）
> **范围**：仅后端。前端 UI 等 F3-B 单独切

## 目标

把 PRD 第 4.4 节里说的「编辑页」需要的所有后端能力做完：

- trips 表新增 `GET /trips/:id` 返回**带派生摘要**
- 新增 `PATCH /trips/:id/summary` 一次更新基础字段 + transport / stay 摘要
- `POST /trips` 创建时自动从 `is_default=true` 的模板拷贝 checklist
- 事件级 CRUD（V1 前端不消费，但开放给 V1.x）
- checklist CRUD + 模板列表

完成后 curl 能够：

```
1. POST /trips → 自动拷出默认 checklist_items
2. GET /trips/:id → 返回 trip 字段 + summary {transport, stay}
3. PATCH /trips/:id/summary → 同时更新 title/note + upsert transport/stay events
4. GET /trips/:id/events → 列出多事件
5. CRUD checklist-items / 列模板
```

## 不做的事

- 不做前端（F3-B）
- 不做 AI 抽取（F5/F6）
- 不做日历视图聚合接口（V1 PRD 里其实也没列日历，留作后续）
- 不做事件冲突检测（同时间两条 transport 之类）

## 数据模型增量

### 0003_trip_events.py

详细字段见 `docs/data-model.md` §2。

要点：
- `meta` 列用 `JSONB`，server_default `'{}'::jsonb`
- 索引 `(user_id, trip_id, start_at)` + `(user_id, trip_id, event_type, start_at)` + `(user_id, deleted_at)`
- CHECK：`event_type IN (...)` / `status IN (...)` / `source IN (...)` / `end_at IS NULL OR end_at >= start_at`
- FK：`trip_id → trips.id ON DELETE CASCADE`、`user_id → users.id ON DELETE CASCADE`

### 0004_checklist.py

详细字段见 `docs/data-model.md` §3 / §4。

两张表：
- `checklist_templates`（无 user_id，全局种子）
- `checklist_items`（用户实例）

种子数据通过同一份迁移 INSERT 18 项（见 §3 表格）。

CHECK：`category IN ('document','electronics','clothing','medicine','food','home','pet','task','other')`

UNIQUE：`(trip_id, label)` on `checklist_items`。

## 后端实现要点

### 目录增量

```
backend/app/
├── models/
│   ├── trip_event.py
│   └── checklist.py        # ChecklistTemplate + ChecklistItem 同文件
├── schemas/
│   ├── trip_event.py       # TripEventOut / TripEventCreate / TripEventPatch / 摘要内嵌 schema
│   ├── trip_summary.py     # TripDetailOut（trip + summary）/ TripSummaryPatch
│   └── checklist.py
├── services/
│   ├── trip_summary.py     # derive_summary / apply_summary_patch
│   └── checklist_seed.py   # 创建 trip 时拷默认模板
└── routes/
    ├── trip_events.py      # /trips/:id/events 和 /events/:id
    ├── trip_summary.py     # /trips/:id (改写 GET) / /trips/:id/summary
    └── checklist.py        # /checklist-items + /checklist-templates
```

### Schema 关键定义

```python
# 摘要嵌套
class TripTransportSummary(BaseModel):
    eventId: UUID | None
    mode: TransportMode | None      # flight | train | bus | car
    departAt: datetime | None
    arriveAt: datetime | None

class TripStaySummary(BaseModel):
    eventId: UUID | None
    hotelName: str | None
    checkinAt: datetime | None
    checkoutAt: datetime | None

# GET /trips/:id 返回这个
class TripDetailOut(TripOut):
    summary: TripSummaryOut       # transport + stay

# PATCH /trips/:id/summary 接受这个
class TripSummaryPatchIn(BaseModel):
    # 顶级字段（同 TripPatch 的子集）
    title: str | None
    destinationCity: str | None
    note: str | None
    startDate: date | None
    endDate: date | None
    timezone: str | None
    # 摘要段
    transport: TripTransportPatch | None  # null 表示删除现有 transport event
    stay: TripStayPatch | None
```

### 摘要派生 service

```python
async def derive_summary(session, trip_id):
    """从 events 衍生 transport / stay 摘要"""
    # 取首条 transport
    transport = await session.scalar(
        select(TripEvent)
        .where(TripEvent.trip_id == trip_id, TripEvent.event_type == 'transport',
               TripEvent.deleted_at.is_(None))
        .order_by(TripEvent.start_at, TripEvent.sort_order)
        .limit(1)
    )
    # 取首条 stay
    stay = await session.scalar(...)
    return TripSummaryOut(transport=..., stay=...)
```

### 摘要 PATCH service

```python
async def apply_summary_patch(session, trip, payload):
    # 1. 更新 trip 顶级字段
    if payload.title: trip.title = payload.title
    # ...

    # 2. transport 段：upsert 或 软删
    existing = await find_first_event(trip.id, 'transport')
    if payload.transport is None and 'transport' in payload.model_fields_set:
        # 显式传 null：软删
        if existing: existing.deleted_at = now()
    elif payload.transport is not None:
        if existing:
            apply_patch(existing, payload.transport)
        else:
            create_event(trip, 'transport', payload.transport)

    # 3. stay 段：同上
    # ...

    await session.commit()
```

**关键约定**：PATCH body 里
- 不传 `transport` 字段 → 不动 transport
- 传 `transport: null` → 软删 transport event
- 传 `transport: {...}` → upsert

### 创建 trip 时的 checklist 拷贝

修改 F2 的 `POST /trips` 在同事务内执行：

```python
trip = Trip(...)
session.add(trip)
await session.flush()  # 拿到 trip.id

# 拷模板
templates = await session.scalars(
    select(ChecklistTemplate).where(ChecklistTemplate.is_default == True)
)
for t in templates:
    session.add(ChecklistItem(
        user_id=user.id,
        trip_id=trip.id,
        label=t.label,
        category=t.category,
        sort_order=t.sort_order,
        source='template',
        template_id=t.id,
    ))

await session.commit()
```

### 路由清单

| Method | Path | 说明 |
|---|---|---|
| GET | `/api/v1/trips/{id}` | **改写**：返回 TripDetailOut（含 summary） |
| PATCH | `/api/v1/trips/{id}/summary` | 摘要级更新 |
| GET | `/api/v1/trips/{id}/events` | 列事件，按 start_at |
| POST | `/api/v1/trips/{id}/events` | 加任意事件 |
| PATCH | `/api/v1/events/{id}` | 改事件 |
| DELETE | `/api/v1/events/{id}` | 软删 |
| GET | `/api/v1/trips/{id}/checklist-items` | 列清单 |
| POST | `/api/v1/trips/{id}/checklist-items` | 加项 |
| PATCH | `/api/v1/checklist-items/{id}` | 改 label / checked / sort_order |
| DELETE | `/api/v1/checklist-items/{id}` | 硬删 |
| GET | `/api/v1/checklist-templates` | 列模板（用于「从模板添加」） |

### 错误约定

- 422：Pydantic 校验失败
- 404：trip / event / checklist 不存在 / 跨用户 / 软删
- 400：业务规则失败（事件 start_at 落在 trip 区间外、checklist label 重复等）
- 401：未登录

## 落地步骤

1. **0003 迁移**：trip_events 表 + 索引 + check + FK
2. **TripEvent ORM** + 模型导出
3. **0004 迁移**：checklist_templates + checklist_items + 18 项种子数据
4. **Checklist ORM** + 模型导出
5. **schemas**：trip_event / trip_summary / checklist 三组
6. **services**：derive_summary + apply_summary_patch + checklist_seed
7. **改 POST /trips**：创建时拷默认 checklist
8. **改 GET /trips/:id**：返回 TripDetailOut（含 summary）
9. **新增 PATCH /trips/:id/summary**
10. **事件级 CRUD 路由**：trip_events.py
11. **checklist 路由**：checklist.py
12. **后端手测**：完整 curl 矩阵（见验收清单）

## 验收清单

### 数据库
- [ ] 0003 迁移成功，trip_events 表三个索引到位
- [ ] 0004 迁移成功，checklist_templates 18 项种子全部落库
- [ ] checklist_items 的 `(trip_id, label)` UNIQUE 生效

### POST /trips
- [ ] 创建 trip 后立刻 GET checklist-items 能看到 N 项 default 模板拷贝
- [ ] 拷贝项 source='template'、template_id 指向源模板

### GET /trips/:id
- [ ] 无任何事件时 summary.transport / summary.stay 都为 null
- [ ] 创建 1 条 transport event 后，GET 能看到 summary.transport 填充
- [ ] 创建多条 transport event 后，summary 取 start_at 最早那条

### PATCH /trips/:id/summary
- [ ] 同时更新 title 和 transport 段：trip.title 改、events 表 upsert 一条 transport
- [ ] 第二次 PATCH 同样的 transport 段：events 表是 UPDATE 不是 INSERT（看 updated_at 改、id 不变）
- [ ] PATCH `transport: null` → 现有 transport event 软删（deleted_at 落时间）
- [ ] PATCH 不传 transport 字段 → 现有 transport 不动
- [ ] PATCH stay 同样规则
- [ ] 跨用户访问该接口 404

### 事件级 CRUD
- [ ] POST /trips/:id/events 创建 activity 类型事件成功
- [ ] GET 按 start_at 排序
- [ ] PATCH 改 title 持久化
- [ ] DELETE 软删（GET 看不到）
- [ ] 跨用户操作 404

### checklist
- [ ] GET 返回当前 trip 的 items，按 sort_order
- [ ] POST 加新项，UNIQUE (trip_id, label) 重名返回 400
- [ ] PATCH checked 字段切换
- [ ] DELETE 硬删
- [ ] GET /checklist-templates 列出 18 项

## 风险 / 已知坑

| 项 | 说明 |
|---|---|
| Pydantic「null vs unset」语义 | PATCH 区分「显式 null = 删」和「字段不传 = 不动」需要用 `model_fields_set` 判断 |
| upsert 事务边界 | summary patch 涉及多张表多条记录，必须在一个事务里成功或失败 |
| 模板拷贝失败 | POST /trips 拷模板要么全成功要么 trip 也不创建，注意事务 |
| 跨时区 | events.start_at 存 UTC，前端按 trip.timezone 渲染；后端不在边界做转换 |
| 软删一致性 | 所有 events 查询都要 `AND deleted_at IS NULL` |
| 0004 种子 update 路径 | 后续要加新模板项靠新写迁移 INSERT；不要改 0004，否则下游环境 alembic 检测不到差异 |
