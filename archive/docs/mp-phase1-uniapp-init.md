# CandyTravel MP Phase 1: uni-app 工程初始化

## 产出位置

- 小程序子工程：`/Users/lunarjan/workspace/candy-travel/miniapp`

## 当前已完成

1. 使用官方 `uni-app Vue3 + Vite + TS` 模板初始化子工程
2. 建立 4 个首发页面的路由骨架
   - `pages/home/index`
   - `pages/calendar/index`
   - `pages/edit/index`
   - `pages/ai/index`
3. 更新 `pages.json`，把首发 4 页注册进小程序页面清单
4. 补了基础 `App.vue` 与页面占位内容，方便后续逐页迁业务
5. 在 `manifest.json` 里预留了 `mp-weixin.appid`

## 你需要补的内容

- 把 `miniapp/src/manifest.json` 里的 `__FILL_WITH_WECHAT_APPID__` 替换成真实 AppID
- 安装依赖
- 启动微信小程序构建

## 本地启动

```bash
cd /Users/lunarjan/workspace/candy-travel/miniapp
npm install
npm run dev:mp-weixin
```

## 下一步建议

1. 先把共享仓库里已经跑通的 `tripStore` 抽成可复用数据层
2. 先迁 `Calendar` 和 `Edit`，因为这两页的 CRUD 已经在 Web 版闭环
3. 再迁 `Home` 和 `AI`，让小程序版本先形成完整首发链路
