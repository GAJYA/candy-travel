# CandyTravel 功能切片路线图

> 配套文档：`docs/prd.md`
> 用法：PRD 是总纲，本文档是落地节奏。每完成一个 F 阶段再开下一个，避免一口气写死所有细节。

## 切片原则

- **依赖优先**：登录是所有业务的前提，先于业务功能；首页依赖已有数据，放最后
- **简单优先**：文本 AI 比图片 AI 简单，先验证链路再扩展输入形态
- **手动优先**：所有 AI 自动化能力，先有手动 fallback 再做自动
- **每片闭环**：每个 F 阶段产出 = 功能切片文档 + 数据模型增量 + 接口契约 + UI 验收

## 切片顺序

| 阶段 | 功能 | 为什么排这里 | 产出位置 |
|---|---|---|---|
| **F0** | 工程骨架 | FastAPI + PG + Alembic + uni-app 跑通 hello world，没业务但走通部署 | `docs/features/F0-skeleton.md` |
| **F1** | 微信登录 | 所有后续接口都要 `user_id`，登录是前提 | `docs/features/F1-auth.md` |
| **F2** | 行程基础 CRUD（手动） | 最小骨架：建 / 改 / 删 trip，先不做 days/events/packing。让用户"能用" | `docs/features/F2-trip-crud.md` |
| **F3** | 日 + 事件 + 打包清单 | 把行程内部维度补全 | `docs/features/F3-trip-detail.md` |
| **F4** | 日历视图 | 纯读视图，依赖 F3 已有数据 | `docs/features/F4-calendar.md` |
| **F5** | AI 文本解析 | 文本比图片简单，先验证 parse → confirm → commit 链路 | `docs/features/F5-ai-text.md` |
| **F6** | AI 图片解析 | 在 F5 链路上换 LLM 调用方式（多模态 / OCR） | `docs/features/F6-ai-image.md` |
| **F7** | 首页聚合 + 统计 | 等前面都有数据了，首页才有东西可展示 | `docs/features/F7-home.md` |

## 每片应包含的内容

每个 `docs/features/Fx-xxx.md` 建议至少有：

1. **目标用户故事**：以「作为 X 用户，我想…，以便…」格式列 2~3 条
2. **UI 草图**：文字描述即可，不强求设计稿；列出页面 / 弹层 / 关键交互
3. **数据模型增量**：本片新增 / 修改的表与字段，配 Alembic 迁移命名
4. **接口契约**：本片涉及的 endpoint、Pydantic 请求 / 响应 schema、示例 payload
5. **验收清单**：勾选式 checklist，跑通后才能进入下一片
6. **明确不做**：本片刻意延后的事项，避免 scope creep

## 进度追踪

- [x] F0 工程骨架（完成于 2026-05-01）
- [x] F1 微信登录（完成于 2026-05-01）
- [x] F2 行程基础 CRUD（完成于 2026-05-01，仅后端）
- [ ] F3 日 + 事件 + 打包清单
- [ ] F4 日历视图
- [ ] F5 AI 文本解析
- [ ] F6 AI 图片解析
- [ ] F7 首页聚合 + 统计

## 备注

- 顺序不是绝对的，遇到外部阻塞（如 LLM 选型未定）可以临时跳片，但要在本文档显式标记
- 任何 F 阶段如果在实现中发现 PRD 总纲有错，回头改 PRD，不要在功能切片里偷偷偏离
- 每完成一片在对应行打勾，并在底部追加一句「Fx 完成于 YYYY-MM-DD」备忘
