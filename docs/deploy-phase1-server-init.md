# Deploy Phase 1: 服务器初始化 + Nginx / HTTPS / 域名接入

## 目标

把现有 `backend/` 最小服务部署到一台 Ubuntu 服务器上，先形成一个可被小程序真机联调使用的测试环境基线。

当前已知环境：

- 域名：`www.willer.tech`
- 服务器 IP：`43.167.191.235`
- 登录用户：`ubuntu`
- 后端目录：`backend/`
- 后端默认端口：`8787`
- 健康检查：`GET /healthz`、`GET /api/v1/healthz`

## 这一轮交付物

- `ops/scripts/bootstrap-ubuntu.sh`
- `ops/nginx/candy-travel.conf.example`
- `ops/systemd/candy-travel-backend.service.example`
- `ops/env/backend.env.example`

这些文件都是模板，不包含真实密钥、证书或生产值。

## 推荐目录约定

服务器建议统一落到：

- 代码目录：`/srv/candy-travel/app`
- 后端目录：`/srv/candy-travel/app/backend`
- 环境变量：`/srv/candy-travel/shared/backend.env`
- 日志目录：`/var/log/candy-travel`

## 建议部署顺序

1. 初始化服务器基础环境
2. 安装 Node.js 20、Nginx、Certbot
3. 上传代码到 `/srv/candy-travel/app`
4. 在 `backend/` 下安装依赖并构建
5. 把 `ops/env/backend.env.example` 复制为服务器私有 `backend.env`
6. 按模板创建 `systemd` 服务
7. 按模板创建 Nginx 站点配置并反代到 `127.0.0.1:8787`
8. 申请并接入 HTTPS 证书
9. 验证 `https://www.willer.tech/healthz`
10. 再去做小程序合法域名配置和真机联调

## 前置确认

### 1. ICP 备案

小程序正式请求域名通常要求已备案域名，`www.willer.tech` 需要先确认备案状态。

### 2. HTTPS 证书

必须提供有效 HTTPS，建议直接使用 Let's Encrypt。

### 3. 环境定位

需要确认这台机器现在是：

- 测试环境
- 正式环境
- 先测试后转正式

如果暂时只有一台机器，建议先按“测试环境优先”的方式配置，避免过早把路径和密钥管理写死成生产形态。

### 4. 小程序后台配置

部署完成后，还要在微信小程序后台配置合法域名：

- request 合法域名
- upload 合法域名
- download 合法域名（如后续需要）

## 当前不在这轮范围内

- 数据库安装与迁移
- 对象存储
- CI/CD
- 进程日志聚合
- 真正的生产级密钥管理

这轮只解决“服务可启动、域名可访问、健康检查可探活”。
