# Deploy Phase 1: 服务器实际执行清单

## 目标

把 `docs/deploy-phase1-server-init.md` 里的模板落成一次可执行流程，目标结果是：

- 服务器上有可运行的 `backend/` 服务
- `systemd` 可托管后端进程
- Nginx 已反代到 `127.0.0.1:8787`
- `https://www.willer.tech/healthz` 可访问

## 执行前确认

在真正上服务器之前，先确认这 4 件事：

1. `www.willer.tech` 已解析到 `43.167.191.235`
2. 域名已完成 ICP 备案，或明确当前仅用于开发测试
3. 服务器允许 `80/443` 入站
4. 你手上的 SSH key 可正常登录 `ubuntu@43.167.191.235`

## 服务器执行步骤

### 1. 登录服务器

```bash
ssh -i ./ssh_key.pem ubuntu@43.167.191.235
```

### 2. 切 root 并执行初始化脚本

先把仓库里的脚本传上去，或直接在服务器上复制脚本内容执行。

```bash
sudo bash /srv/candy-travel/app/ops/scripts/bootstrap-ubuntu.sh
```

如果代码还没上传，先只保证服务器上有这些目录：

- `/srv/candy-travel/app`
- `/srv/candy-travel/shared`
- `/var/log/candy-travel`

### 3. 上传代码并安装后端依赖

```bash
cd /srv/candy-travel/app/backend
npm install
npm run build
```

### 4. 写服务器私有环境变量

```bash
cp /srv/candy-travel/app/ops/env/backend.env.example /srv/candy-travel/shared/backend.env
vim /srv/candy-travel/shared/backend.env
```

至少确认：

- `APP_BASE_URL=https://www.willer.tech`
- `PORT=8787`

### 5. 安装 systemd 服务

```bash
sudo cp /srv/candy-travel/app/ops/systemd/candy-travel-backend.service.example /etc/systemd/system/candy-travel-backend.service
sudo systemctl daemon-reload
sudo systemctl enable candy-travel-backend
sudo systemctl start candy-travel-backend
sudo systemctl status candy-travel-backend --no-pager
```

### 6. 安装 Nginx 站点配置

```bash
sudo cp /srv/candy-travel/app/ops/nginx/candy-travel.conf.example /etc/nginx/sites-available/candy-travel.conf
sudo ln -sf /etc/nginx/sites-available/candy-travel.conf /etc/nginx/sites-enabled/candy-travel.conf
sudo nginx -t
sudo systemctl reload nginx
```

### 7. 申请 HTTPS 证书

```bash
sudo certbot --nginx -d www.willer.tech
```

### 8. 验证健康检查

```bash
curl -i https://www.willer.tech/healthz
curl -i https://www.willer.tech/api/v1/healthz
```

## 失败时先看哪里

### systemd 起不来

先看：

```bash
sudo journalctl -u candy-travel-backend -n 100 --no-pager
```

### Nginx 配置不通过

先看：

```bash
sudo nginx -t
```

### 域名通但接口 502

先看后端是否真的监听在 `127.0.0.1:8787`：

```bash
ss -ltnp | grep 8787
```

### HTTPS 签发失败

优先检查：

- DNS 是否已生效
- `80/443` 是否对外放通
- 域名是否指向当前服务器

## 联调前收口

只有下面 5 项都满足，才建议开始小程序真机联调：

1. `https://www.willer.tech/healthz` 返回 200
2. `https://www.willer.tech/api/v1/healthz` 返回 200
3. `systemd` 重启后服务可自动拉起
4. Nginx reload 不报错
5. 小程序后台已配置合法 request 域名
