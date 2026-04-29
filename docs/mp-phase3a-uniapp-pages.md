# MP Phase 3A: 首页 / 日历 / 计划编辑 迁移到 uni-app

## 这轮范围

在 `miniapp/` 工程骨架和共享数据层已经可用的前提下，先把三个首发页面迁成 **可跑主链路** 的 uni-app 页面：

- 首页 `pages/home/index`
- 日历页 `pages/calendar/index`
- 计划编辑页 `pages/edit/index`

目标不是一轮做完所有视觉细节，而是先闭上：

1. 首页查看 trip 概览
2. 进入某个 trip 的日历页
3. 修改 TripDay / TripEvent
4. 进入计划编辑页修改 Trip 和打包清单

## 迁移方式

### 1. 不重复造一套 miniapp store

miniapp 页面直接复用共享层：

- `@shared/store/tripStore`
- `@shared/data/homeOverview`
- `@shared/types`

为此在 `miniapp` 中新增了 `@shared` alias，指向仓库根目录的 `src/`。

### 2. 页面按“主链路优先”迁移

#### 首页

- 从共享 `tripStore` 读取 `tripList`
- 复用 `homeOverview` 的倒计时和统计派生逻辑
- 点击卡片可跳转到：
  - 日历页
  - 计划编辑页

#### 日历页

- 读取 `selectedTrip.days / selectedTrip.events`
- 支持：
  - 切换日期
  - 保存当天摘要
  - 删除当天
  - 新增活动
  - 删除活动

#### 计划编辑页

- 编辑 Trip 基础字段：
  - 标题
  - 出发城市
  - 目的地
  - 交通方式
  - 酒店
  - 旅行笔记
- 管理打包清单：
  - 勾选
  - 新增
  - 删除

## 当前结论

这轮结束后，uni-app 侧已经不再只是静态骨架，而是开始真正吃共享数据层，具备最小“查看 + 编辑”的主链路。

后续建议：

1. 与 AI 页迁移保持同一套导航和数据读写习惯
2. 下一轮再补页面细节和小程序体验优化
3. 如果后端要接入，优先保持 `TripStore` 对页面的调用口径不变
