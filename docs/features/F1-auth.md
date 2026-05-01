# F1 — 微信登录

> 状态：设计中
> 依赖：F0 工程骨架
> 后续：F2 行程基础 CRUD（所有业务接口都依赖此片产出的 `current_user` 依赖）

## 目标

跑通完整的微信登录链路，让所有后续接口都能拿到稳定的 `user_id`：

```
[微信小程序]                       [后端]                         [微信服务器]
   │ wx.login() → code              │                              │
   │  ──────────────────────────►  │                              │
   │   POST /auth/wechat/login      │                              │
   │   body: { code }               │                              │
   │                                │  GET /sns/jscode2session     │
   │                                │  ──────────────────────────► │
   │                                │  ◄────────────────────────── │
   │                                │  { openid, session_key, ... } │
   │                                │  upsert user, sign JWT        │
   │  ◄──────────────────────────  │                              │
   │   { token, user }              │                              │
   │                                │                              │
   │ uni.setStorageSync('token')    │                              │
   │                                │                              │
   │ 后续请求带 Authorization        │                              │
   │  ──────────────────────────►  │ 验 JWT → 注入 current_user    │
```

完成后能验证：

- 小程序点「登录」→ 后端创建 user → 前端拿到 token + user 信息
- 调 `GET /me` 能拿到当前用户
- token 缺失 / 失效返回 401，前端清 token 跳登录引导
- DB 里 `users` 表里 openid 是 unique，重复登录不重复建 user

## 不做的事（明确延后）

- 不做 refresh token（access token 7 天，过期重走 wx.login 即可）
- 不做手机号授权（`getPhoneNumber`，用到再说）
- 不做用户头像 / 昵称编辑（F1 用微信侧默认值；后续在「我的」页加）
- 不做 unionid 跨应用打通（除非 AppID 绑定开放平台才有 unionid，先存上但不用）
- 不做权限粒度（V1 单角色，所有人都是普通用户）

## 数据模型增量（首份业务迁移）

新建表 `users`：

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| `id` | UUID | PK，default `gen_random_uuid()` | 业务主键 |
| `openid` | VARCHAR(64) | UNIQUE NOT NULL | 微信小程序 openid |
| `unionid` | VARCHAR(64) | nullable, INDEX | 开放平台 unionid，可能为空 |
| `nickname` | VARCHAR(64) | nullable | 用户授权后填 |
| `avatar_url` | VARCHAR(512) | nullable | 用户授权后填 |
| `locale` | VARCHAR(16) | default `zh-CN` | 预留 |
| `timezone` | VARCHAR(32) | default `Asia/Shanghai` | 预留 |
| `created_at` | TIMESTAMPTZ | NOT NULL default now() | |
| `updated_at` | TIMESTAMPTZ | NOT NULL default now() | 更新时刷新 |
| `deleted_at` | TIMESTAMPTZ | nullable | 软删 |

迁移命名：`alembic/versions/0001_users.py`

启用 PG 扩展 `pgcrypto` 以支持 `gen_random_uuid()`。

## 接口契约

### `POST /api/v1/auth/wechat/login`

请求：
```json
{ "code": "0a3..." }
```

响应 200：
```json
{
  "token": "<jwt>",
  "expiresIn": 604800,
  "user": {
    "id": "uuid",
    "nickname": null,
    "avatarUrl": null,
    "locale": "zh-CN",
    "timezone": "Asia/Shanghai"
  }
}
```

响应 400：
```json
{ "message": "wechat code invalid: 40029", "code": "WECHAT_CODE_INVALID" }
```

行为：
1. 调 `code2session` 拿 `openid` / `unionid` / `session_key`
2. 用 `openid` upsert `users`（找到就更新 `unionid`，没有就 insert）
3. 签 JWT：payload 至少含 `{ sub: user.id, exp: now + 7d, iat: now }`
4. session_key 不下发，仅用于后续解密 (V1 不用，预留)

### `GET /api/v1/me`

请求头：`Authorization: Bearer <token>`

响应 200：
```json
{
  "id": "uuid",
  "nickname": null,
  "avatarUrl": null,
  "locale": "zh-CN",
  "timezone": "Asia/Shanghai",
  "createdAt": "2026-05-01T12:00:00Z"
}
```

响应 401：`{ "message": "not authenticated" }` / `{ "message": "token expired" }`

### `PATCH /api/v1/me`

仅允许更新：`nickname` / `avatarUrl` / `locale` / `timezone`

请求：
```json
{ "nickname": "小可", "avatarUrl": "https://..." }
```

响应 200：返回更新后的用户对象。

## 后端实现要点

### 目录增量

```
backend/app/
├── models/
│   ├── __init__.py
│   └── user.py              # SQLAlchemy ORM
├── schemas/
│   ├── __init__.py
│   ├── auth.py              # Pydantic：登录请求 / 响应
│   └── user.py              # Pydantic：UserOut / UserPatch
├── services/
│   ├── __init__.py
│   ├── wechat.py            # code2session HTTP 调用
│   └── jwt_service.py       # 签 / 验 JWT
├── deps.py                  # FastAPI Depends：current_user
└── routes/
    ├── auth.py              # /auth/wechat/login
    └── me.py                # /me
```

### 关键代码点

- `services/wechat.py`：用 `httpx.AsyncClient` 调 `https://api.weixin.qq.com/sns/jscode2session`；处理 `errcode != 0` 的情况，把微信错误码翻译成 4xx
- `services/jwt_service.py`：用 `pyjwt`（要加依赖）；HS256；`exp` 用 unix timestamp
- `deps.py`：`get_current_user` 依赖。从 `Authorization` 头解 JWT → 查 user → 返回；任何失败抛 401
- 所有业务接口（F2 起）都通过 `Depends(get_current_user)` 拿 user，不直接读 token

### 新增依赖

`pyproject.toml` 加：
- `pyjwt>=2.10`
- `python-multipart`（FastAPI form 支持，预留）

## 前端实现要点

### 目录增量

```
miniapp/src/
├── services/
│   ├── api.ts              # 改造：请求拦截器自动塞 token，响应拦截 401
│   └── auth.ts             # wx.login + 调后端 + 缓存 token
├── stores/
│   └── auth.ts             # （V1 暂用 storage + 简单 ref，不上 Pinia）
└── pages/
    └── index/
        └── index.vue       # 改造：未登录时显示「微信登录」按钮；登录后显示 user + healthz
```

### 关键交互

- 冷启动：`onMounted` 读 storage 的 token，有就调 `/me`，无就显示登录按钮
- 点击「登录」：`wx.login()` → `POST /auth/wechat/login` → 写入 storage → 刷新 user
- 401 拦截：`api.ts` 收到 401 时清 token，弹 toast，回到登录态
- 「退出登录」：清 storage，UI 回到未登录态

## 落地步骤

1. **后端：依赖 + 模型 + 迁移**
   - 加 `pyjwt`
   - 写 `models/user.py`
   - 写迁移 `0001_users.py`
   - `alembic upgrade head` 验证 `users` 表落库
2. **后端：services**
   - `wechat.py`：code2session
   - `jwt_service.py`：encode / decode
3. **后端：routes**
   - `routes/auth.py` → `/auth/wechat/login`
   - `routes/me.py` → `GET /me` / `PATCH /me`
   - `deps.py` → `get_current_user`
   - 注册到 `main.py`
4. **后端：手测**
   - 用一个真实 code（小程序里 console.log 出来）跑一次完整登录
5. **前端：API 改造**
   - `api.ts` 加拦截器（token 注入 + 401 处理）
   - `auth.ts` 封装登录流程
6. **前端：首页改造**
   - 未登录态 + 登录后态
7. **联调**
   - 在小程序里点登录，看后端日志和数据库 `users` 表
8. **验收清单全过 → 合并**

## 验收清单

- [ ] `users` 表通过 alembic 迁移落库，含 openid unique 索引
- [ ] 用真实 code 调 `/auth/wechat/login` 成功，返回 token + user
- [ ] 同一个微信号第二次登录不创建新 user
- [ ] 错误的 code 返回 400 + 微信错误码
- [ ] 带 token 调 `/me` 返回当前用户
- [ ] 不带 token / 错误 token 调 `/me` 返回 401
- [ ] 过期 token（手动伪造一个 exp 在过去的）调 `/me` 返回 401
- [ ] 小程序点「登录」按钮 → 看到 user 信息出现
- [ ] 小程序冷启动有 token 时直接显示 user 信息
- [ ] 小程序「退出登录」清掉 token 回到未登录态

## 风险 / 已知坑

| 项 | 说明 |
|---|---|
| code 一次性 | 5min 有效，调过就废，前端不能缓存 |
| code2session 频控 | 高频调用会触发 45011，后端要做 IP / openid 维度限流（V1 先不做，记录 TODO） |
| 时钟漂移 | JWT exp 校验依赖服务端时间，确保服务器 NTP 同步 |
| openid 唯一性 | 必须建 UNIQUE 索引，避免并发 upsert 撞车 |
| AppSecret 泄露 | 永远不下发到小程序代码；如曾泄露立刻在公众平台重置 |
| session_key 失效 | 用户重新登录后旧的失效；V1 不用 session_key 解密数据，问题不大 |
| Pylance 红线 | VSCode 解释器要选 backend/.venv，已在 .vscode/settings.json 钉死 |
