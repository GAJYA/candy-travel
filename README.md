# CandyTravel

个人旅行规划工具：微信小程序前端 + FastAPI 后端 + PostgreSQL。

> 状态：F0 工程骨架（仅 healthz 链路）
> 设计文档：[`docs/prd.md`](docs/prd.md) · [`docs/roadmap.md`](docs/roadmap.md) · [`docs/features/`](docs/features/)
> 旧代码归档：[`archive/`](archive/)（保留参考，不再维护）

## 快速开始（本地开发）

需要：Docker、`uv`、Node.js 18+、微信开发者工具

```bash
# 1. 起 PG + Redis
docker compose up -d

# 2. 起后端（端口 8000）
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload

# 3. 起小程序
cd miniapp
npm install
npm run dev:mp-weixin
# 然后用微信开发者工具打开 miniapp/dist/dev/mp-weixin
```

健康检查：

```bash
curl http://localhost:8000/api/v1/healthz
```

## 工程布局

```
candy-travel/
├── backend/        # FastAPI 后端
├── miniapp/        # uni-app 微信小程序
├── docs/           # PRD / 路线图 / 功能切片
├── archive/        # 旧代码归档
└── docker-compose.yml
```
