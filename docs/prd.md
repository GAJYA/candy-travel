# CandyTravel 产品需求文档（PRD）

> 版本：V1（重写版）
> 上一版：`archive/docs/prd.md`（Web 原型 + uni-app + Fastify + 文件存储）
> 本版变化：放弃 Web 原型，单端聚焦微信小程序；后端切到 FastAPI + PostgreSQL；V1 起做真实多用户。

---

## 1. 产品定位

CandyTravel 是一款面向**个人用户的轻量旅行规划工具**。

核心价值：把"模糊的旅行想法"和"散乱的票据/文本"快速整理成一份**可以照着执行的行程**。

### V1 做的事

1. 看下一次出行的倒计时与概览
2. 按天 / 按事件维护行程
3. 用 AI 把一段文字（行程描述、票据、聊天记录），或截图，转成结构化数据，补充入行程中，比如机票截图中有出行方式，时间。酒店截图中有酒店名和入住离开时间等。
4. 维护目的地、交通、酒店、笔记、打包清单
5. 微信登录，保证个人数据私密

---

## 2. 用户与场景

### 目标用户

方便记录和规划行程，快速看到当前路行计划，解决不同订票平台之间信息不共享的问题。

### 典型场景

- **出行前**：建一个 trip，填好起止日期、目的地、交通方式、酒店
- **接收行程文本**：把朋友发的、AI 助手生成的、订票确认邮件粘进 AI 页，自动抽出 trip 草稿 + 事件 + 打包提示
- **出行前几天**：检查每日安排、勾选打包清单
- **旅行中**：在日历页查看当天事件
- **旅行后**：trip 状态置为 completed，归档保留

---

## 3. 信息架构

四个主 Tab + 一个二级编辑页：

| Tab | 页面 | 解决什么 |
|---|---|---|
| 首页 | `pages/home` | 倒计时 + upcoming trips + 整体统计 |
| 日历 | `pages/calendar` | 按月看日，按天看事件 |
| 行程 | `pages/trip` | AI图片，文本 → 行程草稿 → 导入 -> 手动调整 |
| 我的 | `pages/profile` | 用户信息、设置、登录态 |

二级页：

- `pages/edit`：从首页 / 日历进入，维护单次行程的全部字段
- `pages/login`（或弹层）：未登录拦截

---

## 4. 功能需求

### 4.1 首页（Home）

**核心元素**

- 下一次行程倒计时（天 / 时 / 分），带目的地城市
- upcoming trips 列表（最多 3 条）或日历：标题、目的地、出发日期、状态、出行方式图标
- 总览统计：已规划城市数、行程总数（V1 距离可后端粗算或先返回 0）
- 入口：进入某次行程编辑页 / 日历页；新建行程

**验收点**

- 当无 upcoming trip 时，倒计时与统计走兜底空态，不报错
- 行程状态文案：草稿 / 规划中 / 已确认 / 已完成 / 已归档
- 未登录时显示登录引导，不调用业务接口

### 4.2 日历（Calendar）

**核心元素**

- 月视图：标记有事件的日期、当日高亮
- 选中某天后：显示当日 summary、hint、highlight 标签和事件列表（活动 / 餐饮 / 交通 / 住宿）
- 支持新建 / 编辑 / 删除单天事件
- 一次只看一个 trip 的日历（V1 不做跨 trip 合并视图）

**验收点**

- 选中日期超出 trip 起止范围时给出明确提示
- 月份切换时事件标记同步刷新
- 当用户只有 1 个 trip，自动选中；多个时显示 trip 切换器

### 4.3 AI 导入（AI Import）

两段式：**parse → confirm → commit**。

**流程**

1. 用户粘贴文本（V1 必做）/ 上传图片（V1 可降级 stub）
2. 后端创建 `ai_import_job`，调用 LLM 抽取后返回 `extractedPayloadJson`：
   - `tripDraft`：title / startDate / endDate / originCity / destinationCity / hotelName / note，每个字段带 `confidence`（high / medium / low）
   - `items`：交通 / 活动事件（带置信度）
   - `packingHints`：建议的打包清单
   - `warnings`：解析过程中的可疑点
3. 前端展示草稿，用户确认 / 修改
4. 调用 commit 落库为真实 trip / events / packing items

**验收点**

- 用户可选「作为新 trip」或「合并到已有 trip」
- 抽取失败 / 异常时给到明确文案和重试入口
- 低置信度字段在 UI 上要有视觉区分（如黄色 badge）
- 同一 job 重复 commit **必须幂等**，不重复入库
- 单次抽取超时上限 30s；失败的 job 状态为 `failed` 并保留错误信息

### 4.4 编辑页（Edit Trip）

围绕一个 trip 维护：

- **基本信息**：title、起止日期、出发城市、目的地、主要交通方式、酒店、笔记、封面、状态
- **日列表（trip_days）**：日期、summary、hint、highlight tag、排序
- **事件列表（trip_events）**：交通 / 住宿 / 活动 / 提醒，含起止时间、地点、参考编号
- **打包清单（packing_items）**：分类（证件 / 电子 / 服饰 / 药品 / 食品 / 其他）、勾选状态、排序

**验收点**

- 字段更新走 `PATCH`，不全量提交
- 删除事件 / 日 / 打包项需二次确认
- 起止日期变更时，越界的 trip_days 提示用户处理（保留 / 删除 / 改日期）
- 所有写操作在前端做乐观更新，失败回滚 + toast

### 4.5 用户与认证（V1 必做）

**登录链路**

1. 小程序调用 `wx.login()` 拿到 `code`
2. 调用后端 `POST /api/v1/auth/wechat/login`，body: `{ code }`
3. 后端用 `code2session` 换 `openid` / `unionid`，找到或创建 user
4. 后端签发 JWT（含 `userId`，过期时间 7 天），返回给小程序
5. 小程序持久化到 `uni.setStorageSync('token', ...)`，所有后续请求带 `Authorization: Bearer <token>`

**用户信息授权**

- 首次登录后引导用户授权头像、昵称（`<button open-type="chooseAvatar">` / `nickname` 输入）
- 不授权时使用默认头像 + 系统昵称，不阻塞功能

**验收点**

- token 失效 / 缺失时统一返回 401，前端跳登录引导
- 未登录用户进入首页 / 日历 / AI 时给登录引导，不直接 401
- 用户数据严格按 `user_id` 隔离，不存在跨用户访问

---

## 5. 数据模型（业务视角）

> 详细字段、约束、索引见 `docs/data-model.md`（待编写）。这里仅列实体清单。

### 核心实体

- `users`：openid（唯一）、unionid、nickname、avatar_url、locale、timezone
- `trips`：聚合根，承载首页 / 日历 / 编辑三个视图
- `trip_days`：当天摘要、提示、高亮标签
- `trip_events`：统一承载交通 / 住宿 / 活动 / 提醒
- `packing_items`：打包清单
- `ai_import_jobs`：AI 抽取任务，job + commit 两段式

### 关键约束

- `trips.start_date <= trips.end_date`
- `trip_days.date` 必须在 trip 区间内
- `trip_events.trip_id` 与其挂载的 `trip_day.trip_id` 必须一致
- `ai_import_jobs` commit 后必须幂等
- 所有业务表必须含 `user_id`，并以 `user_id + 主键` 建复合索引
- 不做硬删除，使用 `deleted_at` 软删

### 枚举

| 字段 | 取值 |
|---|---|
| `trip.status` | `draft / planning / confirmed / completed / archived` |
| `trip.primary_transport_mode` | `flight / train / bus / car` |
| `trip.created_via` | `manual / ai_import` |
| `trip_event.event_type` | `transport / stay / activity / reminder` |
| `trip_event.status` | `draft / confirmed / canceled` |
| `trip_event.source` | `manual / ai_extracted` |
| `packing_item.category` | `document / electronics / clothing / medicine / food / other` |
| `packing_item.source` | `manual / ai_generated` |
| `ai_import_job.input_type` | `text / image` |
| `ai_import_job.status` | `pending / processing / parsed / committed / failed` |

---

## 6. API 契约（概览）

> 详细 schema 见 `docs/api.md`（待编写）。所有接口走 `/api/v1/*`，请求/响应 camelCase，日期 `YYYY-MM-DD`，时间戳 ISO 8601。

### 认证

- `POST /auth/wechat/login` — 用 code 换 token
- `POST /auth/refresh` — 刷新 token
- `GET /me` — 当前用户信息
- `PATCH /me` — 更新昵称、头像、locale、timezone

### 首页

- `GET /home` — upcoming + stats 聚合

### 行程

- `GET /trips` — 行程列表（支持 `status` / `keyword` 过滤）
- `POST /trips`
- `GET /trips/:tripId`
- `PATCH /trips/:tripId`
- `DELETE /trips/:tripId`（软删）

### 日历与日

- `GET /trips/:tripId/calendar?month=YYYY-MM`
- `GET /trips/:tripId/days/:date`
- `POST /trips/:tripId/days`
- `PATCH /days/:dayId`
- `DELETE /days/:dayId`

### 行程事件

- `POST /trips/:tripId/events`
- `PATCH /events/:eventId`
- `DELETE /events/:eventId`

### 打包清单

- `GET /trips/:tripId/packing-items`
- `POST /trips/:tripId/packing-items`
- `PATCH /packing-items/:itemId`
- `DELETE /packing-items/:itemId`

### AI 导入

- `POST /ai-import-jobs` — 创建并同步抽取（V1 不上异步队列）
- `GET /ai-import-jobs/:jobId`
- `POST /ai-import-jobs/:jobId/commit` — 落库（幂等）

### 错误约定

- 4xx：`{ "message": string, "code"?: string, "details"?: object }`，前端 toast 直读 `message`
- 5xx：服务器日志 + 通用错误文案
- 401：未登录 / token 失效 → 前端跳登录
- 403：跨用户访问 → 前端 toast「无权访问」

---

## 7. 技术栈

### 7.1 前端：微信小程序

- **基座**：uni-app（Vue 3 + Vite + TypeScript）
- **目标平台**：仅 `mp-weixin`（V1 不做 H5 / 其他小程序）
- **状态管理**：Pinia（按 trip 聚合根分 store）
- **样式**：uni 内置 + 单文件 scoped style
- **请求层**：封装 `uni.request`，统一塞 token、统一错误处理
- **本地缓存**：`uni.setStorageSync` 持久化 token + 最近一次 home 数据（用于冷启动占位）

### 7.2 后端：FastAPI + PostgreSQL

- **运行时**：Python 3.11+
- **框架**：FastAPI + Uvicorn（生产用 Gunicorn + UvicornWorker）
- **ORM**：SQLAlchemy 2.0（async）+ Alembic 迁移
- **校验**：Pydantic v2（所有请求 / 响应 schema 显式声明）
- **数据库**：PostgreSQL 15+
- **缓存 / 限流**：Redis（V1 用于 AI job 限流和登录态校验缓存）
- **AI**：后端代理调用 LLM，模型可替换；通过 `LLM_PROVIDER` env 切换；统一抽象成 `LlmClient` 接口
- **观测**：结构化日志（JSON）+ 健康检查 `/healthz`、`/api/v1/healthz`

### 7.3 部署

- 单台 Ubuntu Server 起步
- Nginx 终结 HTTPS，反代到 FastAPI（systemd 守护）
- PostgreSQL / Redis 同机部署，预留迁移到独立实例的能力
- 静态资源（用户头像等）走对象存储（V1 可先用本地磁盘 + Nginx）

---

## 8. 非功能需求

| 维度 | 要求 |
|---|---|
| 性能 | 首页冷启动 ≤ 1.5s；常用接口 P95 < 300ms；AI 抽取超时 30s |
| 可用性 | 服务月可用率 ≥ 99%；后端 crash 由 systemd 自动拉起 |
| 安全 | 全站 HTTPS；JWT 7 天过期；用户数据严格按 user_id 隔离；不记录敏感 PII 到日志 |
| 隐私 | 行程内容是个人数据，V1 不做分享、不向第三方导出；AI 抽取请求向 LLM 厂商发送的内容需脱敏（去掉手机号、身份证号） |
| 兼容性 | 微信基础库 ≥ 2.27（覆盖近 2 年微信版本） |
| 可观测 | 关键接口打点：登录、AI parse、AI commit、trip 创建；错误率 / 延迟可查 |
| 数据可恢复 | PostgreSQL 每日备份，保留 7 天 |

---

## 9. V1 验收清单

- [ ] 微信登录跑通：新用户首次登录创建 user，老用户登录返回同一 user
- [ ] 首页能看到至少 1 条 upcoming trip 和正确倒计时
- [ ] 日历页能切月、能查看任意一天事件
- [ ] AI 页能贴文本 → 看草稿 → 一键导入为 trip，重复 commit 幂等
- [ ] 编辑页能完整维护 trip / day / event / packing item
- [ ] 401 / 403 处理符合预期
- [ ] 数据库迁移可重复执行，回滚有方案
- [ ] 后端 `/healthz` 在生产可用，Nginx + systemd 守护
- [ ] 小程序提交微信审核版本可通过基础库审核

---

## 10. 后续路线（V1 之外）

| 阶段 | 内容 |
|---|---|
| V1.1 | AI 图片票据 OCR；行程导出（PDF / 图片）；分享只读链接 |
| V1.2 | 行程模板 / 复用；常用打包清单模板 |
| V2 | 多人协同；离线优先（本地写 + 同步 + 冲突解决）；H5 端 |

---

## 11. 待办（PRD 自身）

新版 PRD 的细化文档建议拆成：

- `docs/data-model.md` — PostgreSQL DDL、字段类型、索引、约束
- `docs/api.md` — 完整 API schema（含 Pydantic 模型）
- `docs/tech-design.md` — FastAPI 工程结构、目录组织、模块边界
- `docs/auth.md` — 微信登录链路、JWT 签发与刷新
- `docs/ai.md` — LLM 抽取 prompt 设计、置信度评估、成本与超时控制
- `docs/deploy.md` — 部署拓扑、CI/CD、备份与恢复
