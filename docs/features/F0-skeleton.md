# F0 — 工程骨架

> 状态：设计中
> 依赖：无
> 后续：F1 微信登录依赖此片完成

## 目标

在不写任何业务逻辑的前提下，把以下链路打通：

```
[微信开发者工具]
       │ uni.request
       ▼
 [FastAPI :8000] ──► [PostgreSQL] (Docker)
       │
       └──► [Redis] (Docker)
```

完成后你能做到：

- `docker compose up -d` 起 PG + Redis
- `uv run uvicorn app.main:app --reload` 起后端
- `curl localhost:8000/api/v1/healthz` 返回 `{"status":"ok","db":"ok","redis":"ok"}`
- uni-app 在 mp-weixin 编译运行，首页发请求拿到 `healthz` 返回，渲染在屏幕上

## 不做的事

- 不接入微信登录（F1）
- 不写业务表（trips/events/...）
- 不部署到生产（先本地）
- 不做 CI（等业务稳定再加）

## 工程布局

```
candy-travel/
├── archive/                       # 旧代码归档（保留，不动）
├── docs/
│   ├── prd.md
│   ├── roadmap.md
│   └── features/
│       └── F0-skeleton.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI 入口
│   │   ├── config.py              # pydantic-settings
│   │   ├── db.py                  # SQLAlchemy async engine
│   │   ├── redis_client.py        # Redis 连接
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py          # /healthz, /api/v1/healthz
│   ├── alembic/                   # 迁移目录（先初始化空仓）
│   ├── alembic.ini
│   ├── pyproject.toml             # uv 管理依赖
│   ├── .env.example
│   └── README.md
├── miniapp/
│   ├── src/
│   │   ├── pages/
│   │   │   └── index/             # F0 用：调 healthz 显示结果
│   │   │       ├── index.vue
│   │   │       └── index.json
│   │   ├── services/
│   │   │   └── api.ts             # uni.request 简单封装
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── manifest.json          # 含 mp-weixin appid（不入库）
│   │   ├── pages.json
│   │   └── env.d.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md
├── docker-compose.yml             # PG + Redis
├── .gitignore
└── README.md                      # 仓库总入口
```

## 后端依赖（pyproject.toml）

核心：
- `fastapi`
- `uvicorn[standard]`
- `sqlalchemy>=2.0`
- `asyncpg`（PG 驱动）
- `alembic`
- `pydantic>=2`
- `pydantic-settings`
- `redis>=5`（含 asyncio 支持）
- `httpx`（F1 调 code2session 用，F0 先装上）

dev：
- `pytest`
- `pytest-asyncio`
- `ruff`（lint + format）

## 环境变量（backend/.env.example）

```
ENV=dev
DATABASE_URL=postgresql+asyncpg://candy:candy@localhost:5432/candy
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-me-in-prod
WECHAT_APPID=
WECHAT_APPSECRET=
```

> AppID / AppSecret 在 F1 才会用，F0 留空即可。`.env` 不入库，`.env.example` 入库。

## docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: candy
      POSTGRES_PASSWORD: candy
      POSTGRES_DB: candy
    ports: ["5432:5432"]
    volumes:
      - candy_pg_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    ports: ["6379:6379"]
    volumes:
      - candy_redis_data:/data

volumes:
  candy_pg_data:
  candy_redis_data:
```

## 接口契约（F0 唯一接口）

`GET /api/v1/healthz`

Response:
```json
{
  "status": "ok",
  "db": "ok",
  "redis": "ok",
  "version": "0.1.0"
}
```

实现要点：
- 用一个 `SELECT 1` 探活 PG
- 用 `PING` 探活 Redis
- 任意一个失败则返回 503，body 里显示哪个组件挂了

## 小程序侧（uni-app）

页面：`pages/index/index.vue`

行为：
- onLoad 调 `GET ${API_BASE}/api/v1/healthz`
- 把返回 JSON 渲染到屏幕（`<text>{{ healthData }}</text>` 或简单卡片）
- 失败时显示错误信息

`API_BASE` 读取 `import.meta.env.VITE_API_BASE_URL`，默认 `http://localhost:8000`。

> 真机调试时 `http://` 不允许，需在微信开发者工具的「详情 → 本地设置」里勾「不校验合法域名」（仅本地）。

## 落地步骤（执行顺序）

按这个顺序一步步来，每步独立验证：

1. **仓库基础**：根目录 `.gitignore`、`README.md`、`docker-compose.yml`
2. **后端骨架**：`backend/` 用 `uv init`，写依赖、`config.py`、`main.py`、`health.py`
3. **起 Docker**：`docker compose up -d`，验证 PG/Redis 端口可连
4. **后端跑通**：`uv run uvicorn app.main:app --reload`，curl `healthz` 返回 ok
5. **Alembic 初始化**：`alembic init alembic`，先不写迁移，只验证连得上 DB
6. **小程序骨架**：`miniapp/` 用 uni-app Vue 3 + TS 模板初始化
7. **填 AppID**：`miniapp/src/manifest.json` 写真实 AppID
8. **小程序跑通**：微信开发者工具打开 `miniapp/dist/dev/mp-weixin`，看到 healthz 数据
9. **首次提交**：git commit 一份「F0 骨架」

## 验收清单

- [ ] `docker compose up -d` 后 `psql` 和 `redis-cli` 都能连通
- [ ] `curl http://localhost:8000/api/v1/healthz` 返回 `status: ok`
- [ ] 把 PG 容器停掉后，`healthz` 返回 503 并标注 db 挂了
- [ ] 微信开发者工具能正常打开 `miniapp/dist/dev/mp-weixin`
- [ ] 小程序首页显示从后端拿到的 healthz JSON
- [ ] `backend/.env`、`miniapp/project.private.config.json` 都在 `.gitignore`
- [ ] 仓库根 README 写清楚「怎么把项目跑起来」三步走

## 风险 / 已知坑

| 项 | 说明 |
|---|---|
| 微信开发者工具 localhost 限制 | 真机不行，模拟器需勾「不校验合法域名」 |
| asyncpg vs psycopg | 选 asyncpg，FastAPI async 链路更顺 |
| Alembic + async engine | Alembic 默认是 sync，需要在 env.py 里用 `connection.run_sync` 或者另开一个 sync engine |
| uni-app 模板 | 用官方 `vue3-ts` 模板，避免后续 TS 类型不全 |
