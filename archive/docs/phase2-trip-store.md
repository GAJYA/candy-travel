# Phase 2: Trip / Day / Event Store 与本地持久化

## 路径

- Store 实现：`src/store/tripStore.ts`
- 本地存储 key：`candy-travel-trip-store-v1`

## 当前职责

这层只解决公共数据底座，不直接绑定某一个页面：

- Trip 聚合对象
- TripDay 按天摘要
- TripEvent 活动/交通/提醒
- TripPackingItem 打包清单
- localStorage 持久化
- 基础 CRUD action

## 对后续页面的支持

### 首页

- 读取 `tripList` / `selectedTrip`
- 计算最近旅行、upcoming trips、统计信息

### 日历页

- 读取 `selectedTrip.days`
- 读取 `selectedTrip.events`
- 用 `upsertTripDay` / `upsertTripEvent` / `removeTripEvent` 做 CRUD

### 计划编辑页

- 用 `updateTrip` 更新目的地、酒店、备注、交通方式
- 用 `upsertPackingItem` / `togglePackingItem` / `removePackingItem` 管理清单

### AI 提取确认流

- AI 结果确认后直接调用 `createTrip` 或 `upsertTripEvent`
- 需要补某一天摘要时调用 `ensureTripDay`

## 已提供的公开方法

- `selectTrip`
- `createTrip`
- `updateTrip`
- `upsertTripDay`
- `ensureTripDay`
- `removeTripDay`
- `upsertTripEvent`
- `removeTripEvent`
- `upsertPackingItem`
- `togglePackingItem`
- `removePackingItem`
- `resetTripStore`

## 当前约束

- Store 先走前端本地持久化，不依赖后端。
- 种子数据只是让页面先能跑通，不代表最终业务数据结构已经冻结。
- 后面如果接真实接口，建议优先保持 Trip 聚合结构不变，再把持久化层从 localStorage 替换成 API。
