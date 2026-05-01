# BE Phase 1: 后端服务骨架初始化

## 本轮产物

新增目录：

- `backend/`

当前包含：

- `package.json`
- `tsconfig.json`
- `.env.example`
- `README.md`
- `src/config.ts`
- `src/server.ts`
- `src/index.ts`
- `src/routes/health.ts`

## 当前能力

### 1. 环境配置模板

通过 `.env.example` 提供最小配置项：

- `NODE_ENV`
- `PORT`
- `HOST`
- `LOG_LEVEL`
- `APP_NAME`
- `APP_BASE_URL`

### 2. 启动入口

通过 `src/index.ts` 启动 Fastify 服务。

### 3. 健康检查

已提供：

- `GET /healthz`
- `GET /api/v1/healthz`

返回内容包含：

- `ok`
- `service`
- `timestamp`
- `uptimeSeconds`

## 设计意图

- 先把服务跑起来，再往里加 `Trip / Day / Event / PackingItem / AI import` 路由。
- 后端和前端工程解耦，避免直接混在根目录的 Vite 配置中。
- Phase 1 只解决“可启动、可配置、可探活”，不在这一轮直接带数据库和业务路由。

## 下一步建议

1. Phase 2 增加 `api/v1` 路由注册入口
2. Phase 3 接入配置化 logger / error handler
3. Phase 4 接 Trip 查询与更新的最小 mock repository
