# F2 — 行程基础 CRUD（后端）

> 状态：设计中
> 依赖：F1 微信登录（拿到 `current_user`）
> 后续：F3（events + checklist + 摘要派生）依赖此片产出的 trip 实体
> **范围**：仅后端。前端 UI 等 F3 一起做，避免走两趟界面

## 目标

跑通 trips 表的最小 CRUD 链路：

```
[curl + JWT]
   POST   /api/v1/trips             创建
   GET    /api/v1/trips             列出当前用户的 trips
   GET    /api/v1/trips/:id         详情
   PATCH  /api/v1/trips/:id         局部更新
   DELETE /api/v1/trips/:id         软删（deleted_at = now()）
```

完成后能验证：

- 创建 trip 自动绑定 `current_user.id`
- 列表只返回当前用户的 trip，不会跨用户泄漏
- 软删后 GET / list 看不到这条
- 跨用户 GET 别人的 trip 返回 404（不是 403，不暴露存在性）
- 起止日期不合法（start > end）返回 422

## 不做的事

- 不做 events / checklist（F3）
- 不做摘要派生（F3）
- 不做前端 UI（等 F3）
- 不做分页（V1 用户的 trip 量级小，直接返回全部，按 `start_date DESC` 排序）
- 不做关键词搜索 / 状态过滤参数（V1 客户端拿全量自己过滤；真要后端筛后续再加）
- 不做硬删除接口（DELETE 永远是软删）
- 不做 `cover_image_url` 上传，只接受 URL

## 数据模型增量

新建表 `trips`，详细字段见 `docs/data-model.md` §1。

迁移命名：`alembic/versions/0002_trips.py`

## 后端实现要点

### 目录增量

```
backend/app/
├── models/
│   └── trip.py              # ORM
├── schemas/
│   └── trip.py              # TripCreate / TripOut / TripPatch
└── routes/
    └── trips.py             # /trips CRUD
```

### Schema 字段映射

```python
class TripCreate(BaseModel):
    title: str                                  # required
    destination_city: str | None = None
    status: TripStatus = TripStatus.draft
    start_date: date | None = None
    end_date: date | None = None
    cover_image_url: str | None = None
    note: str | None = None
    timezone: str = "Asia/Shanghai"
    # created_via 不开放给客户端，永远 'manual'（AI 路径在 F5/F6 单独走）

class TripOut(BaseModel):
    id: UUID
    title: str
    destination_city: str | None
    status: TripStatus
    start_date: date | None
    end_date: date | None
    cover_image_url: str | None
    note: str | None
    timezone: str
    created_via: TripCreatedVia
    created_at: datetime
    updated_at: datetime

class TripPatch(BaseModel):
    # 所有字段可选；status 走 PATCH 也行（提交、归档）
    title: str | None = None
    destination_city: str | None = None
    status: TripStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    cover_image_url: str | None = None
    note: str | None = None
    timezone: str | None = None
```

camelCase 转换走 Pydantic alias，与 F1 一致。

### 校验规则

应用层（Pydantic + service）校验，DB CHECK 兜底：

- POST：`start_date <= end_date`（任一为空跳过）
- PATCH：合并后的 `start_date <= end_date` 也要满足；要把 patch 字段和现有 trip 数据合并后再判
- `title` 长度 1~128
- `timezone` 不在 PG 已知列表中先不卡（V1 不做严格校验，让 IANA 字符串透传）

### 路由约定

| Method | Path | 说明 |
|---|---|---|
| POST | `/api/v1/trips` | 201 + `TripOut` |
| GET | `/api/v1/trips` | 200 + `list[TripOut]`，按 `start_date DESC NULLS LAST, created_at DESC` |
| GET | `/api/v1/trips/{trip_id}` | 200 + `TripOut`；非自己 / 软删 / 不存在 → 404 |
| PATCH | `/api/v1/trips/{trip_id}` | 200 + `TripOut` |
| DELETE | `/api/v1/trips/{trip_id}` | 204；幂等（已删再删返回 204） |

所有路由都通过 `Depends(get_current_user)` 拿 user，并在 query 中 `WHERE user_id = current_user.id`。

### 错误约定

- 422：Pydantic 校验失败（FastAPI 默认）
- 404：`{ "detail": "trip not found" }`（不存在 / 软删 / 跨用户）
- 401：未登录
- 400：业务校验失败（如 `start > end`）
- 500：兜底

## 落地步骤

1. **ORM**：写 `models/trip.py`，并在 `models/__init__.py` 导出
2. **迁移**：写 `0002_trips.py`，`alembic upgrade head` 验证表落库
3. **Pydantic schemas**：`schemas/trip.py`，camelCase 别名一致 F1 风格
4. **service / repo（如需）**：复杂查询封装，简单的直接在 route 里写
5. **路由**：`routes/trips.py`，注册到 `main.py`
6. **后端手测**：用真实 JWT 跑全套 CRUD（含跨用户隔离）
7. **写最小 pytest 用例**（可选，V1 没要求 TDD，但越早建测试越好）

## 验收清单

- [ ] `trips` 表通过 alembic 迁移落库，含 status / created_via 的 CHECK 约束
- [ ] POST 创建 trip 成功，`user_id` = 当前用户
- [ ] POST 提交 `start_date > end_date` 返回 422 / 400
- [ ] GET list 只返回当前用户、未软删的 trip
- [ ] GET detail 拿别人的 trip 返回 404
- [ ] PATCH 更新 title 持久化
- [ ] PATCH 把 status 改成 archived 持久化
- [ ] DELETE 后 GET list / detail 都看不到
- [ ] 已删除的 trip 再 DELETE 返回 204（幂等）
- [ ] 未登录调任意 trips 接口返回 401

## 风险 / 已知坑

| 项 | 说明 |
|---|---|
| 跨用户 enumeration | 所有 GET 必须 `AND user_id = current_user.id`；漏一处就泄漏 |
| 软删一致性 | list / detail / patch / delete 都要带 `deleted_at IS NULL`，否则会处理到僵尸记录 |
| `start_date <= end_date` PATCH 合并校验 | PATCH 只传 start_date 时，要拉现有 end_date 校验 |
| 时区透传 | `timezone` 字符串没做严格 IANA 校验，V1 信任前端 |
| OpenAPI 文档 alias | response_model_by_alias=True 必须写，否则 /docs 看的是 snake_case |
