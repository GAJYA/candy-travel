# CandyTravel Backend

FastAPI + PostgreSQL + Redis. 用 [`uv`](https://docs.astral.sh/uv/) 管理依赖。

## 本地运行

```bash
# 仓库根目录先起 PG / Redis
docker compose up -d

# 进 backend
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

打开 `http://localhost:8000/docs` 看 OpenAPI。

## 健康检查

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/api/v1/healthz
```

## 目录结构

```
backend/
├── app/
│   ├── main.py           # FastAPI 入口
│   ├── config.py         # 环境配置
│   ├── db.py             # SQLAlchemy async engine
│   ├── redis_client.py   # Redis 连接
│   └── routes/
│       └── health.py
├── alembic/              # 迁移（F0 仅初始化，不写迁移）
├── pyproject.toml
└── .env.example
```
