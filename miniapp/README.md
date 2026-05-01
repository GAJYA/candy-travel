# CandyTravel Miniapp

uni-app（Vue 3 + Vite + TS）→ 微信小程序。

## 本地运行

```bash
npm install
cp .env.example .env       # 可选，覆盖 VITE_API_BASE_URL
npm run dev:mp-weixin
```

然后用**微信开发者工具**打开 `dist/dev/mp-weixin/` 目录。

## 配置 AppID

`src/manifest.json` 里的 `mp-weixin.appid` 是空的，需要本地填入你的小程序 AppID。
该文件入库（项目共享），AppID 是公开的不算秘密。但**`appsecret` 不要写在小程序代码里**，只能放后端 `.env`。

> 微信开发者工具的 `project.private.config.json` 已经在 `.gitignore`，每个开发者本地维护。

## 本机调试 vs 真机调试

- **模拟器**：默认 `http://localhost:8000/api/v1`，需要在微信开发者工具「详情 → 本地设置」勾选**「不校验合法域名」**
- **真机预览**：手机和电脑需在同一局域网，把 `.env` 里 `VITE_API_BASE_URL` 改成 `http://<你的电脑 IP>:8000/api/v1`，并确保后端用 `--host 0.0.0.0` 启动
- **生产**：必须 HTTPS，并把域名加入小程序后台「开发管理 → 服务器域名 → request 合法域名」

## 目录结构

```
miniapp/src/
├── App.vue
├── main.ts
├── manifest.json        # mp-weixin appid
├── pages.json           # 路由
├── pages/
│   └── index/           # F0 临时首页：调 healthz
├── services/
│   └── api.ts           # uni.request 封装
└── static/
```
