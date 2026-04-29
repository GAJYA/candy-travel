# MP Phase 2: uni-app 共享数据层迁移

## 目标

把现有 Web 版已经跑通的共享数据层，先收敛成一层 **uni-app / Web 可共用** 的基础设施，而不是在页面迁移时再把数据逻辑抄一遍。

## 这轮代码调整

### 1. 共享领域类型上提

此前 `TripDay / TripEvent / TripPackingItem / TripRecord` 等核心类型定义在 `src/store/tripStore.ts` 内部。

这轮统一提升到 `src/types.ts`：

- `TripRecord`
- `TripDay`
- `TripEvent`
- `TripPackingItem`
- `TripSource / TripEventType / TripEventStatus / PackingCategory / PackingSource`

这样后续 uni-app 页面、store、service、mock repository 都可以直接共享，不需要从 store 实现文件里反向 import 类型。

### 2. 本地持久化抽象成平台适配层

新增：

- `src/platform/storage.ts`

职责：

- 优先走 `uni.getStorageSync / uni.setStorageSync`
- Web 环境自动回退到 `localStorage`

这一步的意义是：

- 当前 H5 还能继续工作
- 后续迁 uni-app 时，store 层不需要再把 `window.localStorage` 全量替换

### 3. 现有数据读取层接入平台适配

已接入：

- `src/store/tripStore.ts`
- `src/data/homeOverview.ts`

这意味着：

- Trip 主 store 的持久化已经不再直接依赖浏览器全局 `window`
- 首页 overview 读取层也已经可以复用同一套适配逻辑

## 当前结论

这一阶段完成后，数据层已经具备“先在 Web 里继续迭代，同时可被 uni-app 复用”的基本条件，但还没有完成真正的小程序页面迁移。

后续建议顺序：

1. Phase 1 的 uni-app 工程骨架先落稳
2. Phase 3A / 3B 页面迁移时直接复用这批类型和存储适配
3. 等小程序端稳定后，再考虑把 store 从当前单例实现继续拆成更明确的 repository + store 组合
