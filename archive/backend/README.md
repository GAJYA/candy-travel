# CandyTravel Backend

最小后端骨架，当前提供：

- 环境配置加载
- Fastify 启动入口
- `/healthz` 健康检查
- `Trip / Day / Event / PackingItem` 的文件型 CRUD API
- AI 文本提取 stub 路由

## 本地启动

1. 安装依赖

```bash
npm install
```

2. 复制环境变量

```bash
cp .env.example .env
```

3. 启动开发服务

```bash
npm run dev
```

## 当前路由

- `GET /healthz`
- `GET /api/v1/healthz`
- `GET /api/v1/home`
- `GET /api/v1/trips`
- `POST /api/v1/trips`
- `GET /api/v1/trips/:tripId`
- `PATCH /api/v1/trips/:tripId`
- `GET /api/v1/trips/:tripId/calendar`
- `GET /api/v1/trips/:tripId/days/:date`
- `POST /api/v1/trips/:tripId/days`
- `PATCH /api/v1/trips/:tripId/days/:dayId`
- `DELETE /api/v1/trips/:tripId/days/:dayId`
- `POST /api/v1/trips/:tripId/events`
- `PATCH /api/v1/events/:eventId`
- `DELETE /api/v1/events/:eventId`
- `GET /api/v1/trips/:tripId/packing-items`
- `POST /api/v1/trips/:tripId/packing-items`
- `PATCH /api/v1/packing-items/:itemId`
- `DELETE /api/v1/packing-items/:itemId`
- `POST /api/v1/ai-import-jobs`
- `GET /api/v1/ai-import-jobs/:jobId`
- `POST /api/v1/ai-import-jobs/:jobId/commit`
