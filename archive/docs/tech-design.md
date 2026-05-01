# CandyTravel 技术设计文档

> 适用版本：V1
> 配套文档：`prd.md`、`v1-data-model-api-draft.md`、`be-phase1-backend-skeleton.md`、`deploy-phase1-server-init.md`

## 1. 系统总览

CandyTravel 由三个工程构成，共享同一份 API 契约：

```
candy-travel/
├── src/                  # Web 原型（Vue 3 + Vite + Tailwind）
├── miniapp/              # 微信小程序（uni-app + Vue 3 + Vite + TS）
├── backend/              # API 服务（Fastify + zod，文件型存储）
├── ops/                  # Nginx / systemd / 部署脚本
└── docs/                 # 阶段文档与契约
```

数据流：

```
[Web 原型 / 微信小程序]
        │  HTTPS  /api/v1/*
        ▼
   [Nginx :443]
        │  reverse_proxy → 127.0.0.1:PORT
        ▼
  [Fastify Backend]  ──────►  data/candy-travel-db.json
        │  AI parse stub
        ▼
  （可选）Gemini API
```

## 2. 前端：Web 原型（`src/`）

- 框架：Vue 3.5（`<script setup lang="ts">`）
- 构建：Vite 5
- 样式：Tailwind CSS 4（`@tailwindcss/vite`）
- 图标：`lucide-vue-next`
- 日历：`v-calendar`
- AI SDK：`@google/genai`（端上 demo 用，生产应走后端中转）

页面结构：

```
src/
├── App.vue
├── components/
│   ├── HomeScreen.vue        # 首页（倒计时 + upcoming + 统计）
│   ├── CalendarScreen.vue    # 日历
│   ├── AIScreen.vue          # AI 导入
│   ├── ProfileScreen.vue     # 我的
│   └── BottomNav.vue         # 底部 4 Tab
├── store/tripStore.ts        # 全局 trip 状态 + 持久化
├── data/                     # 静态/Mock 数据辅助
├── platform/                 # 平台抽象层（Web / MP 兼容）
└── types.ts                  # 类型契约（见 §5）
```

特点：

- `tripStore` 是单源 trip / day / event / packing 状态，配本地持久化（详见 `docs/phase2-trip-store.md`）
- 通过 `platform/` 抽象差异，让同一份 store 能跑在 Web 与 uni-app

## 3. 前端：微信小程序（`miniapp/`）

- 基座：uni-app（Vue 3 + Vite + TS）
- 4 页首发：`pages/home`、`pages/calendar`、`pages/ai`、`pages/edit`（外加占位 `pages/index`）
- 入口配置：`pages.json` / `manifest.json`（mp-weixin appid 在 `manifest.json`）
- 服务层：`src/services/api.ts` 封装 `uni.request` → 暴露 `homeApi` / `tripApi` / `aiImportApi`

API base：

```ts
const DEFAULT_API_BASE_URL = "https://www.willer.tech/api/v1";
export const apiBaseUrl = trimTrailingSlash(import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL);
```

错误处理：自定义 `ApiRequestError(message, statusCode, data)`，4xx/5xx 都抛出，调用方 try/catch 后 toast 即可。

注意事项：

- 真机调试需把后端域名加入小程序后台"合法域名"
- 编辑页历史上踩过 `<input>` 不能直接放在文本流里、需要用 `<view>` 包裹（commit `eb40e6a`）
- `project.config.json` / `project.private.config.json` 不入库（gitignore），由开发者本地维护

## 4. 后端（`backend/`）

- 运行时：Node.js ≥ 18，ESM
- 框架：Fastify 4
- 校验：zod 4
- 存储：**文件型 JSON**（`data/candy-travel-db.json`），单文件持久化，进程内读写

### 4.1 目录结构

```
backend/src/
├── index.ts             # 启动入口（dotenv → server.listen）
├── server.ts            # Fastify 实例 + 路由注册
├── config.ts            # 环境配置加载
└── routes/
    ├── health.ts        # /healthz、/api/v1/healthz
    ├── trips.ts         # trips / days / events / packing-items
    └── ai-import.ts     # ai-import-jobs（含 commit 幂等）
```

### 4.2 路由清单

健康检查：

- `GET /healthz`
- `GET /api/v1/healthz`

业务（参考 `backend/README.md`）：

| Method | Path | 说明 |
|---|---|---|
| GET | `/api/v1/home` | 首页聚合（upcoming + stats） |
| GET / POST | `/api/v1/trips` | trip 列表 / 创建 |
| GET / PATCH | `/api/v1/trips/:tripId` | trip 详情 / 局部更新 |
| GET | `/api/v1/trips/:tripId/calendar?month=YYYY-MM` | 日历视图 |
| GET | `/api/v1/trips/:tripId/days/:date` | 单日详情 |
| POST / PATCH / DELETE | `.../days[/:dayId]` | 日 CRUD |
| POST | `/api/v1/trips/:tripId/events` | 事件创建 |
| PATCH / DELETE | `/api/v1/events/:eventId` | 事件更新 / 删除 |
| GET / POST | `/api/v1/trips/:tripId/packing-items` | 打包清单列表 / 创建 |
| PATCH / DELETE | `/api/v1/packing-items/:itemId` | 打包清单更新 / 删除 |
| POST / GET | `/api/v1/ai-import-jobs[/:jobId]` | AI job 创建 / 查询 |
| POST | `/api/v1/ai-import-jobs/:jobId/commit` | 抽取结果落库（幂等） |

### 4.3 数据契约

请求 / 响应字段使用 **camelCase**；日期：`YYYY-MM-DD`；时间戳：ISO 8601 with offset。

zod schema 摘录（`routes/trips.ts`）：

- `transportMode` ∈ `flight | train | bus | car`
- `tripStatus` ∈ `draft | planning | confirmed | completed | archived`
- `tripEventType` ∈ `transport | stay | activity | reminder`
- `packingCategory` ∈ `document | electronics | clothing | medicine | food | other`

### 4.4 错误约定

- 4xx：`{ "message": string, "error"?: string }`，前端 toast 直接读 `message`
- 5xx：服务器日志 + 通用错误文案
- 校验失败统一走 `ZodError → 400`

### 4.5 AI 抽取（V1 stub）

- `POST /ai-import-jobs` 同步走 stub 解析（V1 不引入异步队列）
- `extractedPayloadJson` 字段带置信度（`high | medium | low`）和 `warnings`
- `commit` 接口对同一 job 必须幂等：返回 `idempotent: true` 时不再重复创建实体

## 5. 共享类型契约

`src/types.ts` 是前端唯一契约源，与后端 zod schema 一一对应：

```ts
export type TripStatus = 'draft' | 'planning' | 'confirmed' | 'completed';
export type TripEventType = 'transport' | 'stay' | 'activity' | 'reminder';
export type PackingCategory = 'document' | 'electronics' | 'clothing' | 'medicine' | 'food' | 'other';

export interface TripRecord {
  id: string;
  title: string;
  status: TripStatus;
  startDate: string;     // YYYY-MM-DD
  endDate: string;
  originCity: string;
  destinationCity: string;
  primaryTransportMode: TransportMode;
  hotelName: string;
  note: string;
  countdownAnchorAt: string;    // ISO datetime
  createdVia: TripSource;
  coverImageUrl?: string;
  days: TripDay[];
  events: TripEvent[];
  packingItems: TripPackingItem[];
  createdAt: string;
  updatedAt: string;
}
```

> ⚠️ 后端 `tripStatusSchema` 还包含 `archived`，前端 `TripStatus` 暂未覆盖。新增 archived 流程时需同步前后端。

## 6. 部署与运维（`ops/`）

参考 `docs/deploy-phase1-server-init.md` 与 `docs/deploy-phase1-server-execution-checklist.md`。

线上拓扑：

- Ubuntu Server
- Nginx 终结 HTTPS（`ops/nginx/candy-travel.conf.example`），反代 `/api/` → 后端 systemd 服务
- 后端用 systemd 守护（`ops/systemd/candy-travel-backend.service.example`）
- 健康检查脚本：`ops/scripts/verify-backend-health.sh`
- 初始化脚本：`ops/scripts/bootstrap-ubuntu.sh`
- 环境变量模板：`ops/env/backend.env.example`

域名 / 证书：`www.willer.tech` 走 HTTPS，小程序合法域名同步。

## 7. 本地开发

```bash
# Web 原型
yarn install
yarn dev          # 默认 :3000

# 后端
cd backend
npm install
cp .env.example .env
npm run dev       # 文件型 DB 写入 backend/data/candy-travel-db.json

# 小程序
cd miniapp
npm install
npm run dev:mp-weixin   # 用微信开发者工具打开 dist/dev/mp-weixin
```

Node.js ≥ 18 是硬性前提（`scripts/check-node.cjs` 在 predev/prebuild 阶段卡住低版本）。

## 8. 已知约束 / 风险

| 项 | 现状 | 风险 |
|---|---|---|
| 存储 | 单文件 JSON | 并发写、容量、查询效率都不可扩展，正式上线前必须替换 |
| 鉴权 | 无 | 所有接口当前是开放的，仅靠 Nginx + 域名隔离 |
| AI 抽取 | stub | 真实模型质量、超时、成本均未做约束 |
| 多端共享类型 | 手工同步 | 前后端契约依赖人肉对齐，后续可考虑 schema 单源生成 |
| 小程序登录 | 未做 | 用户身份缺失，统计、私密数据无法多人化 |

## 9. 演进方向

短期（V1.1）：

- 把 `data/candy-travel-db.json` 替换为 SQLite（保留接口形状）
- 加最小鉴权：小程序 `code2session` + 后端签发 token
- AI 文本抽取接入真实 LLM（带成本和超时上限）

中期（V2）：

- PostgreSQL + Prisma
- 行程模板 / 复用
- 离线优先：前端写本地 → 后台同步 + 冲突解决
- AI 图片票据 OCR

## 10. 相关文档索引

- 数据模型与 API 契约：`docs/v1-data-model-api-draft.md`
- 后端骨架：`docs/be-phase1-backend-skeleton.md`
- 前端实现计划：`docs/phase-1-frontend-implementation-plan.md`
- Trip Store：`docs/phase2-trip-store.md`
- 小程序四页骨架：`docs/mp-phase1-uniapp-init.md`
- 小程序共享数据层：`docs/mp-phase2-shared-data-layer.md`
- 小程序首发四页业务：`docs/mp-phase3a-uniapp-pages.md`
- 小程序后端环境方案：`docs/mp-phase-4-backend-env-plan.md`
- 服务器初始化：`docs/deploy-phase1-server-init.md`
- 部署执行清单：`docs/deploy-phase1-server-execution-checklist.md`
