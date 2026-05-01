# 行程数据模型设计

> 版本：V1
> 配套：`docs/prd.md` §5 / `docs/features/F2-*.md` / `docs/features/F3-*.md`

## 设计立场

**表结构按多事件设计，UI 在 V1 只暴露摘要层。** 这样 DB 一次到位、不需要后续迁移；UI 简洁、不暴露用户暂时不需要的复杂度；V1.x 解锁多事件只需要加 API 路径和 UI 入口，DDL 不动。

具体落到三层：

| 层 | V1 形态 | V1.x 升级路径 |
|---|---|---|
| **DB Schema** | trips + trip_events + packing_*（完整多事件支持） | 不变 |
| **API** | `PATCH /trips/:id/summary` 摘要级；事件级 CRUD（`POST /trips/:id/events` 等）也存在 | API 层不变，前端开始用事件级 CRUD |
| **UI** | 摘要页：单 transport + 单 stay + 备注 + 打包清单 | 增加「添加事件」入口，使用事件级 API |

## 关键决策

1. **聚合根模式**：`trips` 是父，`trip_events` / `packing_items` 挂在它下面
2. **事件统一表**：`trip_events` 一张，`event_type` 区分 transport / stay / activity / reminder，特异字段进 `meta jsonb`
3. **摘要纯派生**：trip 表**不存** `transport_mode` / `depart_at` / `hotel_name` 这种「来自首条 event」的字段；每次查询时从 events 衍生
4. **不存 trip_days**：日级聚合靠 events 实时 GROUP BY
5. **不存 ai_import_jobs**：AI 抽取走纯函数式接口，结果直接喂前端草稿态
6. **单 origin / 单 destination**：跨城靠 events 里的多条 transport
7. **多用户隔离**：所有业务表 NOT NULL 带 `user_id`
8. **软删**：trips / events 用 `deleted_at`；packing_items 硬删
9. **枚举存法**：`VARCHAR + CHECK 约束`，应用层 Pydantic Enum 强类型校验，DDL 兼容性好
10. **检查清单双轨**：`checklist_templates`（全局种子）+ `checklist_items`（用户每 trip 实例）。「检查清单」是广义概念，不限于打包，也包含「锁门、关煤气、宠物水粮」等出门前 task

## 实体关系总图

```
users (F1 ✓)                         checklist_templates (全局种子，无 user_id)
  │                                          │
  └─< trips                                  │
        │                                    │
        ├─< trip_events                      │
        └─< checklist_items >───────────────┘ (template_id 可空)
```

---

## 1. trips

聚合根。**不内联**摘要字段（transport_mode / depart_at / hotel_name 这些都靠 events 衍生）。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | UUID | PK | `gen_random_uuid()` |
| `user_id` | UUID | NOT NULL, FK→users.id | 数据隔离主键 |
| `title` | VARCHAR(128) | NOT NULL | 「京都樱花之旅」 |
| `destination_city` | VARCHAR(64) | nullable | 主目的地，首页/统计用 |
| `status` | VARCHAR(16) | NOT NULL, default `draft`, CHECK | `draft / planning / confirmed / completed / archived` |
| `start_date` | DATE | nullable | 起始日（V1 创建后可未定） |
| `end_date` | DATE | nullable | 结束日 |
| `cover_image_url` | VARCHAR(512) | nullable | 封面 |
| `note` | TEXT | nullable | 行程级备注 |
| `timezone` | VARCHAR(32) | NOT NULL, default `Asia/Shanghai` | events 渲染时区 |
| `created_via` | VARCHAR(16) | NOT NULL, default `manual`, CHECK | `manual / ai_import` |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | nullable | 软删 |

**约束**

- `CHECK (start_date IS NULL OR end_date IS NULL OR start_date <= end_date)`

**索引**

- `(user_id, status, start_date)` —— 首页 upcoming
- `(user_id, deleted_at)` —— 列表过滤软删

---

## 2. trip_events

承载所有事件（transport / stay / activity / reminder）。

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | NOT NULL, FK→users.id | 跨用户校验冗余 |
| `trip_id` | UUID | NOT NULL, FK→trips.id ON DELETE CASCADE | |
| `event_type` | VARCHAR(16) | NOT NULL, CHECK | `transport / stay / activity / reminder` |
| `title` | VARCHAR(128) | NOT NULL | |
| `start_at` | TIMESTAMPTZ | NOT NULL | UTC 存，trip.timezone 展示 |
| `end_at` | TIMESTAMPTZ | nullable | 单点时间事件留空 |
| `location_name` | VARCHAR(128) | nullable | |
| `address` | VARCHAR(256) | nullable | |
| `note` | TEXT | nullable | |
| `meta` | JSONB | NOT NULL, default `'{}'::jsonb` | 类型特异字段 |
| `status` | VARCHAR(16) | NOT NULL, default `confirmed`, CHECK | `draft / confirmed / canceled` |
| `source` | VARCHAR(16) | NOT NULL, default `manual`, CHECK | `manual / ai_extracted` |
| `sort_order` | INTEGER | NOT NULL, default 0 | 同 start_at 内排序 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |
| `deleted_at` | TIMESTAMPTZ | nullable | |

**约束**

- `CHECK (end_at IS NULL OR end_at >= start_at)`
- 业务层校验 `start_at` 落在 trip 区间内

**索引**

- `(user_id, trip_id, start_at)` —— 时间线视图主索引
- `(user_id, trip_id, event_type, start_at)` —— 摘要查询用（取首条 transport / stay）
- `(user_id, deleted_at)`

### `meta` jsonb 按 event_type 约定

```ts
// transport
{
  mode: 'flight' | 'train' | 'bus' | 'car',
  fromCity?: string,
  toCity?: string,
  flightNo?: string,
  trainNo?: string,
  seat?: string,
  refCode?: string
}

// stay
{
  hotelName?: string,
  roomType?: string,
  refCode?: string,
  guests?: number
}

// activity
{
  tags?: string[],
  ticketRef?: string,
  cost?: { amount: number, currency: string }
}

// reminder
{
  remindAt?: string  // ISO，与 start_at 等价
}
```

新字段进 meta 不需要迁移；新 `event_type`（如 V1.1 加「门票」）需要更新 CHECK 约束。

### 时区

- `start_at` / `end_at` 一律 timestamptz（PG 内部 UTC）
- 前端按 `trip.timezone` 渲染
- V1 假设 trip 内所有 events 同时区，跨时区行程暂不切换

---

## 3. checklist_templates（全局种子）

系统预设的常用检查项，**无 user_id**，所有用户共享只读。**广义检查清单**，不止打包：

- 打包类（带什么）
- 家居安全类（出门前检查锁门、电器、煤气）
- 宠物 / 植物类（水粮、清理）
- 事务类（出行前要做的杂事，比如设置邮件自动回复）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | UUID | PK | |
| `label` | VARCHAR(64) | NOT NULL, UNIQUE | 「护照」「锁好门」 |
| `category` | VARCHAR(16) | NOT NULL, CHECK | `document / electronics / clothing / medicine / food / home / pet / task / other` |
| `sort_order` | INTEGER | NOT NULL, default 0 | 同 category 内默认顺序 |
| `is_default` | BOOLEAN | NOT NULL, default false | 新建 trip 时是否自动加入 |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**分类语义**

| category | 用途 | 示例 |
|---|---|---|
| `document` | 证件类 | 护照、身份证、签证 |
| `electronics` | 电子设备 | 手机、充电器、转换插头 |
| `clothing` | 服饰 | 换洗衣物、外套、泳衣 |
| `medicine` | 药品 | 常用药、晕车药 |
| `food` | 食品 | 零食、奶粉 |
| `home` | 家居安全 | 锁门、关煤气、关空调 |
| `pet` | 宠物 / 植物 | 喂食、加水、清理猫砂 |
| `task` | 出行前事务 | 设置邮件自动回复、通知公司 |
| `other` | 其他 | 雨伞、防晒霜 |

**种子数据**通过 alembic 迁移脚本 `INSERT` 一次性灌入，后续要加项继续写迁移。

**初始种子建议**

| label | category | is_default |
|---|---|---|
| 护照 | document | true |
| 身份证 | document | true |
| 手机 | electronics | true |
| 充电器 | electronics | true |
| 充电宝 | electronics | true |
| 牙刷 / 牙膏 | other | true |
| 换洗衣物 | clothing | true |
| 常用药品 | medicine | false |
| 雨伞 | other | false |
| 防晒霜 | other | false |
| 锁好门 | home | true |
| 关煤气 | home | true |
| 拔掉不必要电器 | home | false |
| 关空调 | home | false |
| 喂宠物 / 加水 | pet | false |
| 清理猫砂 | pet | false |
| 给植物浇水 | pet | false |
| 设置邮件自动回复 | task | false |

---

## 4. checklist_items（用户每 trip 的实例）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | UUID | PK | |
| `user_id` | UUID | NOT NULL, FK→users.id | |
| `trip_id` | UUID | NOT NULL, FK→trips.id ON DELETE CASCADE | |
| `label` | VARCHAR(64) | NOT NULL | |
| `checked` | BOOLEAN | NOT NULL, default false | |
| `category` | VARCHAR(16) | NOT NULL, default `other`, CHECK | 同 checklist_templates 9 类 |
| `source` | VARCHAR(16) | NOT NULL, default `manual`, CHECK | `template / manual / ai_generated` |
| `template_id` | UUID | nullable, FK→checklist_templates.id ON DELETE SET NULL | 模板引用，方便统计 |
| `sort_order` | INTEGER | NOT NULL, default 0 | |
| `created_at` | TIMESTAMPTZ | NOT NULL | |
| `updated_at` | TIMESTAMPTZ | NOT NULL | |

**约束**

- UNIQUE `(trip_id, label)` —— 同 trip 内 label 不重复
- 不软删（清单项轻量，硬删可接受）

**索引**

- `(user_id, trip_id, sort_order)`

**新建 trip 时的默认行为**

后端 `POST /trips` 创建 trip 后，同事务内把 `checklist_templates WHERE is_default=true` 全部拷贝成 `checklist_items`：
- `source = 'template'`
- `template_id = templates.id`
- `checked = false`
- `category / sort_order` 继承 template

---

## 5. 摘要派生规则

UI 摘要字段（transportMode / departAt / arriveAt / hotelName / checkinAt / checkoutAt）**不存表**，每次查询时按以下规则从 events 衍生：

```python
def derive_summary(trip):
    transport = first(
        events.where(trip_id=trip.id, event_type='transport', deleted_at IS NULL)
              .order_by(start_at, sort_order)
    )
    stay = first(
        events.where(trip_id=trip.id, event_type='stay', deleted_at IS NULL)
              .order_by(start_at, sort_order)
    )
    return {
        "transportMode":  transport.meta.get("mode")     if transport else None,
        "departAt":       transport.start_at             if transport else None,
        "arriveAt":       transport.end_at               if transport else None,
        "hotelName":      stay.meta.get("hotelName")     if stay else None,
        "checkinAt":      stay.start_at                  if stay else None,
        "checkoutAt":     stay.end_at                    if stay else None,
    }
```

**编辑路径**：前端调 `PATCH /trips/:id/summary`，后端把摘要字段拆成 transport upsert + stay upsert（详见 API 章节）。

---

## 6. API 形态（V1）

### 摘要级（V1 前端只用这套）

- `GET  /trips/:id` — 返回 trip 基础字段 + 派生摘要（transport / stay summary 内嵌）
- `PATCH /trips/:id/summary` — 同时更新基础字段 + 摘要（拆成 events upsert）

`PATCH /trips/:id/summary` 的请求体示例：

```json
{
  "title": "京都樱花之旅",
  "destinationCity": "京都",
  "note": "别忘了带雨伞",
  "transport": {
    "mode": "flight",
    "departAt": "2026-04-10T09:30:00+08:00",
    "arriveAt": "2026-04-10T14:15:00+08:00"
  },
  "stay": {
    "hotelName": "樱花皇宫大酒店",
    "checkinAt": "2026-04-10",
    "checkoutAt": "2026-04-13"
  }
}
```

后端逻辑：
- `transport` 段：找 trip 下首条 `transport` event，存在则 PATCH，不存在则 INSERT；如果整个 `transport` 字段是 `null`，则软删现有的首条 transport
- `stay` 段：同上
- `title / destinationCity / note` 直接更新 trips 表

### 事件级（V1 后端有，前端 V1 不用）

- `POST /trips/:id/events` — 加任意类型事件
- `GET  /trips/:id/events` — 列所有事件（按 start_at 排序）
- `PATCH /events/:id`
- `DELETE /events/:id`（软删）

V1.x 解锁多事件时，前端开始消费这套。

### 检查清单

- `GET /trips/:id/checklist-items`
- `POST /trips/:id/checklist-items` — 加项
- `PATCH /checklist-items/:id` — 改 label / checked / sort_order
- `DELETE /checklist-items/:id`
- `GET /checklist-templates` — 列所有可选模板（V1 用于「从模板添加」入口）

---

## 7. 迁移文件规划

| 序号 | 文件 | 内容 | 阶段 |
|---|---|---|---|
| 0001 | `0001_users.py` | users 表 | F1 ✓ |
| 0002 | `0002_trips.py` | trips 表 + check 约束 + 索引 | F2 |
| 0003 | `0003_trip_events.py` | trip_events 表 + meta jsonb + 索引 | F3 |
| 0004 | `0004_checklist.py` | checklist_templates + checklist_items + 默认种子数据 | F3 |

每张表落库时同步：
- 写 SQLAlchemy ORM model
- 在 `app/models/__init__.py` 导出
- 写 Pydantic schema
- 写 routes / services
- 写最小测试用例

---

## 8. 不引入的表（明确延后）

| 表名 | 旧版 PRD 有 | 不做的原因 |
|---|---|---|
| `trip_days` | ✓ | events GROUP BY 实时算；当天 summary / hint / highlight tag V1 UI 不需要 |
| `ai_import_jobs` | ✓ | AI 抽取走纯函数接口，结果直接喂前端草稿，确认后落 events。重复提交幂等靠前端 idempotency_key 或 UI 防双击 |
| `trip_segments` | (设计选项) | 单 origin / 单 destination 已能覆盖 V1 |
| `users.session_key` | - | V1 不解密微信加密数据 |

---

## 9. 待你拍板的细节

下面几个我先按推荐方案写进了上面的设计，你 review 时如果有不同意见再调：

- [x] **「下一站去哪」字段映射**：暂定 trips.title 存输入值；destination_city 单独字段，用户**可不填**（V1 UI 上「下一站去哪」对应 title；destination_city 留给后期 AI 抽取或编辑页二次输入）
- [x] **出发时间粒度**：单一 datetime（trip_events.start_at = TIMESTAMPTZ）
- [x] **「是否入住酒店」**：靠是否存在 `event_type='stay'` 的事件来判断；UI 摘要 stay 字段空 → 后端软删现有 stay event
- [x] **预设打包模板**：全局种子（packing_templates 无 user_id），用户不可编辑模板，但可在自己的 packing_items 里随意改/删/加
- [ ] enum 用 VARCHAR+check（已采用）
- [ ] cover_image_url 是否做上传：V1 先只接受 URL 外链，上传留 V1.x
- [ ] meta jsonb 是否建 GIN 索引：V1 先不建（不查 meta 内字段）
- [ ] PG 行级安全 RLS：V1 不启，应用层校验已足够

---

## 10. 升级路径预演（V1.x 解锁多事件）

到那个时候要做的事：

1. **API 不变**：事件级 CRUD `POST /trips/:id/events` 等已经在了
2. **UI 加入口**：编辑页加「添加事件」按钮、「事件列表」区
3. **摘要规则不变**：仍是「首条 transport / 首条 stay」；用户加更多事件不影响摘要展示
4. **可能新增**：日历页（按月看当天事件）、事件详情页

DDL 完全不变。这就是为什么 V1 要把表设计好。
