# CandyTravel Phase 1 前端落地方案

## 目标

把当前的单文件 Tab 原型改造成一个可继续接真实数据、可继续拆分实现任务的前端基础盘。

这一阶段不追求把所有功能一次做完，只解决 4 个问题：

1. 页面入口从 `activeTab` 切换变成真实路由
2. 页面共享状态从组件内 mock 数据变成可管理的 store
3. 页面数据各自绑定到明确的数据来源
4. 前端先接一层本地 mock repository，后续再平滑切到真实 API

依赖约束以 [v1-data-model-api-draft.md](/Users/lunarjan/workspace/candy-travel/docs/v1-data-model-api-draft.md) 为准。

## 当前问题

- `src/App.vue` 仍然通过一个 `activeTab` 在 4 个组件间切换，没有页面级路由。
- 首页、日历、AI、编辑页都各自持有写死数据，页面之间没有共享数据源。
- 当前没有统一的领域类型，只存在少量 UI 层类型。
- 后面要做的 `store / CRUD / 首页接真实数据 / AI 提交流`，如果没有前置结构，容易各改各的。

## 方案结论

### 1. 路由层

建议引入 `vue-router`，把当前 4 个一级入口落成真实页面。

推荐路由：

```text
/
├─ /home
├─ /trips/:tripId/calendar
├─ /trips/:tripId/edit
└─ /ai/import
```

补充说明：

- `/` 直接重定向到 `/home`
- 首页只承担总览和最近行程入口
- 日历页和编辑页都绑定到具体 `tripId`
- AI 页先保持独立页面，提交成功后跳到目标 `tripId`

不建议继续保留“Profile = 我的”这种命名方式。路由上直接叫 `edit` 更贴近真实业务语义。

### 2. 壳层拆分

建议把当前 `App.vue` 拆成：

```text
src/
├─ app/
│  ├─ AppShell.vue
│  ├─ AppHeader.vue
│  └─ AppBottomNav.vue
├─ pages/
│  ├─ home/HomePage.vue
│  ├─ calendar/CalendarPage.vue
│  ├─ edit/TripEditPage.vue
│  └─ ai/AIImportPage.vue
└─ router/
   └─ index.ts
```

原则：

- `AppShell` 只处理全局布局、导航和 `RouterView`
- 页面自己负责取数和触发页面级 action
- 现有 `HomeScreen / CalendarScreen / AIScreen / ProfileScreen` 可以先搬到 `pages/` 下，后面再分子组件

### 3. 状态层

建议引入 `pinia`，不要继续靠组件内 `ref/reactive` 持有主数据。

推荐 store 划分：

```text
src/stores/
├─ session.ts
├─ home.ts
├─ trips.ts
├─ calendar.ts
├─ trip-editor.ts
└─ ai-import.ts
```

职责建议：

- `session`
  - 当前用户、当前活跃 `tripId`
- `home`
  - 首页概览、upcoming trips、加载状态
- `trips`
  - trip 实体缓存、按 id 查询、创建/更新 trip
- `calendar`
  - 当前月数据、按天详情、event CRUD
- `trip-editor`
  - 编辑页表单态、packing items、保存草稿
- `ai-import`
  - 提取输入、job 状态、结果确认、commit 流程

### 4. 数据接入层

前端不要直接在 store 里写 fetch。建议先抽一层 repository。

```text
src/services/
├─ api/
│  ├─ home.ts
│  ├─ trips.ts
│  ├─ events.ts
│  ├─ packing-items.ts
│  └─ ai-import.ts
├─ repositories/
│  ├─ home-repository.ts
│  ├─ trip-repository.ts
│  └─ ai-import-repository.ts
└─ mappers/
   └─ trip-mappers.ts
```

阶段策略：

1. 先做 `local mock repository`
2. 返回结构严格对齐 API 契约
3. 等后端 ready，再把 repository 内部实现从 local/mock 替换成 HTTP

这样 `page/store` 层不用跟着重写。

## 页面数据落点

### 首页 `/home`

数据来源：

- `GET /api/v1/home`
- `homeStore.summary`
- `homeStore.upcomingTrips`

页面只关心：

- 最近一次旅行概览
- upcoming trips 列表
- 跳转到对应 trip 的 calendar/edit

当前页面里的“年度统计 / 足迹地图 / 累计里程”可以先保留 UI 壳，但 Phase 1 只要求它们能够降级为空态或 mock adapter 输出。

### 日历页 `/trips/:tripId/calendar`

数据来源：

- `GET /api/v1/trips/:tripId/calendar?month=YYYY-MM`
- `GET /api/v1/trips/:tripId/days/:date`
- `POST/PATCH/DELETE` event

页面只负责：

- 切月
- 选中日期
- 展示当天摘要与 activity 列表
- 打开新增/编辑 activity 流程

日历页应该吃 `calendarStore`，不要再保留组件内 `plansByDate` 常量作为主数据源。

### 编辑页 `/trips/:tripId/edit`

数据来源：

- `GET /api/v1/trips/:tripId`
- `GET /api/v1/trips/:tripId/packing-items`
- `PATCH /api/v1/trips/:tripId`
- packing item CRUD

页面只负责：

- trip 基础信息编辑
- packing items 编辑
- 保存与离开提醒

当前 `ProfileScreen` 要改名成业务编辑页，不再承担“个人中心”语义。

### AI 页 `/ai/import`

数据来源：

- `POST /api/v1/ai-import-jobs`
- `GET /api/v1/ai-import-jobs/:jobId`
- `POST /api/v1/ai-import-jobs/:jobId/commit`

页面只负责：

- 输入文本
- 发起提取
- 展示结果
- 用户确认并提交
- 跳转到对应 trip 的 calendar/edit

## 领域类型建议

建议把 UI 类型和领域类型分开。

```text
src/domain/
├─ trip.ts
├─ trip-day.ts
├─ trip-event.ts
├─ packing-item.ts
└─ ai-import.ts
```

不要继续把页面展示态直接当成领域类型本身。领域对象应直接对齐 `docs/v1-data-model-api-draft.md` 里的实体设计。

## 本地持久化策略

Phase 1 还没接真实后端时，建议这样做：

- repository 先使用 `localStorage` 或 `IndexedDB` 存储 mock 数据
- `sessionStore` 记录当前用户和最近活跃 trip
- `tripEditorStore` 保存未提交草稿
- `aiImportStore` 保存最近一次 job 结果，避免刷新丢失

如果只做最小闭环，优先 `localStorage` 即可，等数据结构稳定后再评估是否切 IndexedDB。

## 实施顺序

### Step 1

引入 `vue-router` 和 `pinia`，完成壳层改造：

- `main.ts` 挂载 router + pinia
- `App.vue` 收缩成 `AppShell`
- 一级入口改成真实路由导航

### Step 2

补领域类型与 repository 层：

- 定义 domain types
- 建立 mock repositories
- 输出统一 mapper

### Step 3

改日历页和编辑页：

- 日历页接 `calendarStore`
- 编辑页接 `tripEditorStore`
- 先打通 trip / event / packing item 的本地 CRUD

### Step 4

改首页：

- 首页从 `homeStore` 取 upcoming trips 和 summary
- 卡片点击跳到具体 trip

### Step 5

改 AI 页：

- 先做文本提取 mock job
- 结果确认后写入 `tripsStore + calendarStore`

## 对后续任务的直接影响

这份方案落地后，后续任务可以这样衔接：

- `Phase 2 Trip / Day / Event store 与本地持久化`
  - 直接承接 `stores + repositories + local persistence`
- `Phase 3A 日历页 + 计划编辑页 CRUD`
  - 直接承接 `calendar/edit` 两页的 store 改造
- `Phase 3B 首页总览接真实数据`
  - 直接承接 `homeStore + /home`
- `Phase 4 AI 文本提取确认流`
  - 直接承接 `ai-import store + commit flow`

## 不建议现在做的事

- 不要在 Phase 1 直接引入复杂后端 SDK
- 不要先上用户体系再做 trip CRUD
- 不要继续把首页、日历、编辑页的数据散落在组件常量里
- 不要把“个人中心”继续当真实产品模块推进

## 一句话结论

Phase 1 的任务不是“再写一版 PRD”，而是把当前原型改造成：

**有真实路由、有统一 store、有稳定数据落点、能平滑从 mock 过渡到 API 的前端应用。**
