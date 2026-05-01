# CandyTravel 产品需求文档（PRD）

> 适用版本：V1（小程序首发 + Web 原型）
> 状态：基于现有代码与历史阶段文档（`be-phase1` / `mp-phase1~3a` / `mp-phase4` / `deploy-phase1`）整理而成。

## 1. 产品定位

CandyTravel 是一款面向**个人用户的轻量旅行规划工具**，核心价值是把"模糊的旅行想法 / 散乱的票据"快速整理成一份**可以照着执行的行程**。

不做的事（V1 边界）：

- 不做 OTA 类预订、支付、票务交易
- 不做多人协同 / 行程社交
- 不做实时机票酒店比价

聚焦做的事：

1. 看下一次出行的倒计时和概览
2. 按天 / 按事件维护行程
3. 用 AI 把一段文字（行程描述、票据）转成结构化行程草稿
4. 维护目的地、交通、酒店、笔记、打包清单

## 2. 用户与场景

主要用户：**有旅行习惯、自己规划行程的个人用户**。

典型场景：

- 出行前 1~4 周：建一个 trip，填好起止日期、目的地、交通方式、酒店
- 收到行程文本（朋友发的、AI 助手生成的、订票确认）：贴进 AI 页，自动抽出 trip 草稿 + 事件 + 打包提示
- 出行前几天：检查每日安排、勾选打包清单
- 旅行中：在日历页查看当天事件
- 旅行后：trip 状态置为 completed，归档

## 3. 核心信息架构

四个主 Tab，对应 4 条核心链路：

| Tab | 页面 | 解决什么 |
|---|---|---|
| 首页 | `HomeScreen` / `pages/home` | 倒计时 + upcoming trips + 整体统计 |
| 日历 | `CalendarScreen` / `pages/calendar` | 按月看日，按天看事件 |
| AI | `AIScreen` / `pages/ai` | 文本 → 行程草稿 → 一键导入 |
| 我的 | `ProfileScreen` / `pages/profile`（Web）| 用户、设置（V1 占位） |

编辑入口：从首页 / 日历进入 `pages/edit`，维护单次行程的全部内容。

## 4. 功能需求

### 4.1 首页（Home）

- 展示**下一次行程倒计时**（天 / 时 / 分）和目的地城市
- 展示 **upcoming trips 列表**（最多 3 条）：标题、目的地、出发日期、状态、出行方式图标（飞机/火车）
- 展示**总览统计**：已规划城市数、行程总数、累计距离
- 入口：进入某次行程的编辑页 / 日历页；新建行程

验收点：

- 当无 upcoming trip 时，倒计时和统计应有兜底空态，不报错
- 行程状态文案：草稿 / 规划中 / 已确认 / 已完成

### 4.2 日历（Calendar）

- 月视图：标记有事件的日期、当日高亮
- 选中某天后：看当日 summary、hint、highlight 标签和事件列表（活动 / 餐饮 / 交通 / 住宿）
- 支持新建 / 编辑 / 删除单天事件
- 一次只看一个 trip 的日历（V1 不做跨 trip 合并视图）

验收点：

- 选中日期超出 trip 起止范围时给出明确提示
- 月份切换时事件标记同步刷新

### 4.3 AI 导入（AI Import）

两段式：**parse → confirm → commit**。

- 用户粘贴一段文字 / 上传图片（V1 仅文本必做，图片可降级为 stub）
- 后端创建 `ai_import_job`，返回 `extractedPayloadJson`：
  - `tripDraft`：title / startDate / endDate / originCity / destinationCity / hotelName / note，每个字段带 `confidence`
  - `items`：抽取出的交通 / 活动事件（带置信度）
  - `packingHints`：建议的打包清单
  - `warnings`：解析过程中的可疑点
- 用户在前端确认 / 修改后调用 commit，落库为真实 trip / events / packing items
- 同一 job 重复 commit 应**幂等**

验收点：

- 用户可以选择把抽取结果"作为新 trip"或"合并到已有 trip"
- 抽取失败 / 异常时给到明确文案和重试入口
- 低置信度字段在 UI 上要有视觉区分

### 4.4 编辑页（Edit Trip）

围绕一个 trip 维护：

- 基本信息：title、起止日期、出发城市、目的地、主要交通方式、酒店、笔记、封面、状态
- 日列表（trip_days）：日期、summary、hint、highlight tag、排序
- 事件列表（trip_events）：交通 / 住宿 / 活动 / 提醒，含起止时间、地点、参考编号
- 打包清单（packing_items）：分类（证件 / 电子 / 服饰 / 药品 / 食品 / 其他）、勾选状态、排序

验收点：

- 字段更新走 `PATCH`，不要全量提交
- 删除事件 / 日 / 打包项需二次确认
- 起止日期变更时，越界的 trip_days 需要提示用户处理

### 4.5 用户与认证（V1 简化）

- V1 暂不做完整的微信登录闭环（保留扩展位）
- 后端用单租户假身份 / 默认 user 跑通；后续阶段再引入微信小程序登录

## 5. 数据模型（业务视角）

详见 `docs/v1-data-model-api-draft.md`。核心实体：

- `users`：昵称、头像、locale、timezone
- `trips`：聚合根，承载首页 / 日历 / 编辑三个视图
- `trip_days`：当天摘要、提示、高亮标签
- `trip_events`：统一承载交通 / 住宿 / 活动 / 提醒
- `packing_items`：打包清单
- `ai_import_jobs`：AI 抽取任务，job + commit 两段式

约束：

- `trips.start_date <= trips.end_date`
- `trip_days.date` 必须在 trip 区间内
- `trip_events.trip_id` 与 `trip_day.trip_id` 必须一致
- `ai_import_jobs` commit 后必须幂等

## 6. 非功能需求

- **多端一致**：Web 原型与微信小程序共享同一份数据模型与 API 契约
- **可离线降级**：网络异常时前端走本地缓存只读
- **错误透传**：后端 4xx 必须带 `message`，前端 toast 直接读
- **私密性**：行程内容是个人数据，V1 不做分享
- **性能**：首页冷启动 ≤ 1.5s（小程序），常用接口 P95 < 300ms

## 7. 当前进度（截至 2026-05）

参考 `docs/` 下阶段文档与 git log：

- ✅ Web 原型已经从 React 重构到 Vue 3
- ✅ 后端骨架（Fastify + zod + 文件存储）已跑通核心 CRUD 和 AI import stub
- ✅ uni-app 小程序四页 + service 层接入真实 API（`www.willer.tech/api/v1`）
- ✅ INT Phase 3 契约对齐已完成
- 🚧 编辑页 UI 仍在迭代（最近修了输入框对齐和容器问题）
- ⏭ 微信登录、AI 图片抽取、生产数据库（替换 JSON 文件存储）尚未开始

## 8. V1 验收清单

- [ ] 首页能看到至少 1 条 upcoming trip 和正确倒计时
- [ ] 日历页能切月、能查看任意一天事件
- [ ] AI 页能贴文本 → 看草稿 → 一键导入为 trip
- [ ] 编辑页能完整维护 trip / day / event / packing item
- [ ] 小程序与 Web 调用同一套后端 API，行为一致
- [ ] 后端 `/healthz` 在生产可用，Nginx + systemd 守护

## 9. 后续路线（V1 之外）

1. 微信小程序登录 + 多用户隔离
2. 文件存储 → PostgreSQL / SQLite 持久层
3. AI 图片票据识别（OCR + LLM）
4. 多人协同行程
5. 离线优先（本地写 + 同步）
