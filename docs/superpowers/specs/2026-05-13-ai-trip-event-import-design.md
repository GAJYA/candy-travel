# AI 自动补充行程事件设计

## 背景

CandyTravel 已经具备行程、同行成员、每日事件和事件编辑能力。sub2api 已部署在 `https://ai.willer.tech/v1`，并验证过文本与图片识别链路可用。下一步要把订单截图识别能力接入行程编辑页，让用户选中一个行程后上传飞机、高铁、酒店等订单截图，由 AI 识别出候选事件，用户编辑或确认后保存到该行程。

## 目标

- 用户在行程编辑页上传订单截图，系统识别交通、住宿和其他可转成行程事件的信息。
- AI 只返回候选事件，不直接写入数据库。
- 用户可以编辑、移除、重新识别候选事件。
- 用户确认后，后端把候选事件保存为 `source=ai_extracted` 的行程事件。
- 图片仅用于本次识别，不落盘、不进对象存储、不保存在数据库。
- 默认 AI 模型使用 `gpt-5.5`。

## 非目标

- 不做订单截图长期存储。
- 不做后台异步任务队列。
- 不做航班、高铁、酒店真实状态查询。
- 不做自动去重合并历史事件，只在确认页提示疑似重复。
- 不做复杂票务、支付、发票、身份证、手机号等敏感信息管理。

## 用户流程

1. 用户进入已有行程的编辑页。
2. 在“每日行程”标题右侧点击 `AI导入`。
3. 小程序弹出上传面板，用户选择 1 到 6 张订单截图。
4. 前端把图片上传到后端识别接口。
5. 后端校验用户对行程有访问权限，校验图片类型与大小，调用 AI。
6. 后端返回候选事件列表和识别警告。
7. 前端展示候选事件确认页。
8. 用户编辑、移除或重新识别。
9. 用户点击“保存到行程”。
10. 前端把编辑后的候选事件提交到导入确认接口。
11. 后端创建 `TripEvent`，事件来源为 `ai_extracted`。
12. 前端刷新每日行程列表。

## 页面草图

```text
行程编辑页
┌────────────────────────────┐
│ 每日行程              AI导入 │
├────────────────────────────┤
│ 5月20日                    │
│ 09:30  ✈️ 上海 → 东京       │
│ 15:00  🏨 入住 XXX 酒店     │
└────────────────────────────┘
```

```text
AI 补充行程
┌────────────────────────────┐
│ 上传订单截图                │
│                            │
│  [＋ 飞机/高铁/酒店订单截图] │
│                            │
│ 支持多张图片，会自动识别交通 │
│ 和住宿信息，不会直接保存。   │
│                            │
│              取消   开始识别 │
└────────────────────────────┘
```

```text
识别到 3 个行程事件
┌────────────────────────────┐
│ ✈️ 航班 MUxxxx              │
│ 5月20日 09:30 - 12:45       │
│ 上海虹桥 → 东京羽田          │
│ 置信度：高                  │
│                 编辑   移除  │
├────────────────────────────┤
│ 🚄 高铁 Gxxxx               │
│ 5月19日 14:00 - 16:20       │
│ 杭州东 → 上海虹桥            │
│                 编辑   移除  │
├────────────────────────────┤
│ 🏨 入住 XXX 酒店             │
│ 5月20日 - 5月23日            │
│ 东京新宿                    │
│                 编辑   移除  │
└────────────────────────────┘

          重新识别     保存到行程
```

## 后端接口

### 识别候选事件

`POST /api/v1/trips/{tripId}/ai/extract-events`

请求使用 `multipart/form-data`：

- `images`: 1 到 6 个图片文件，支持 `image/jpeg`、`image/png`、`image/webp`
- `clientTimezone`: 可选，默认使用行程 `timezone`

后端限制：

- 单张图片最大 8 MB
- 总图片最大 24 MB
- 请求必须携带 CandyTravel 登录 token
- 用户必须能访问该行程
- 图片数据只在请求内存中传给 AI，不写入磁盘和数据库

响应：

```json
{
  "tripId": "uuid",
  "model": "gpt-5.5",
  "events": [
    {
      "clientId": "tmp_1",
      "eventType": "transport",
      "title": "航班 MUxxxx 上海虹桥 → 东京羽田",
      "startAt": "2026-05-20T09:30:00+08:00",
      "endAt": "2026-05-20T12:45:00+09:00",
      "locationName": "上海虹桥国际机场",
      "address": null,
      "note": "到达：东京羽田机场。订单号已省略。",
      "meta": {
        "icon": "plane",
        "allDay": false,
        "orderType": "flight",
        "transportMode": "flight",
        "departurePlace": "上海虹桥",
        "arrivalPlace": "东京羽田",
        "flightNo": "MUxxxx"
      },
      "confidence": "high",
      "warnings": []
    }
  ],
  "warnings": []
}
```

### 保存确认后的事件

`POST /api/v1/trips/{tripId}/ai/import-events`

请求 JSON：

```json
{
  "events": [
    {
      "clientId": "tmp_1",
      "eventType": "transport",
      "title": "航班 MUxxxx 上海虹桥 → 东京羽田",
      "startAt": "2026-05-20T09:30:00+08:00",
      "endAt": "2026-05-20T12:45:00+09:00",
      "locationName": "上海虹桥国际机场",
      "address": null,
      "note": "到达：东京羽田机场",
      "meta": {
        "icon": "plane",
        "allDay": false,
        "orderType": "flight",
        "transportMode": "flight",
        "departurePlace": "上海虹桥",
        "arrivalPlace": "东京羽田",
        "flightNo": "MUxxxx"
      },
      "sortOrder": 0
    }
  ]
}
```

后端创建事件时：

- `source` 固定写为 `ai_extracted`
- `status` 固定写为 `confirmed`
- `user_id` 使用当前登录用户
- `trip_id` 使用路径参数
- 重用现有 `TripEvent` 表，不新增表

## AI 调用

后端配置：

```env
AI_BASE_URL=https://ai.willer.tech/v1
AI_API_KEY=sk-...
AI_MODEL=gpt-5.5
AI_TIMEOUT_SECONDS=60
AI_MAX_IMAGES=6
AI_MAX_IMAGE_MB=8
```

服务边界：

- 新增 `app/services/ai_client.py` 负责调用 OpenAI 兼容接口。
- 新增 `app/services/ai_trip_event_extractor.py` 负责构造 prompt、解析 JSON、校验候选事件。
- 路由层不直接拼 prompt，不直接处理 AI 响应细节。

Prompt 原则：

- 告诉模型当前行程标题、日期范围、timezone。
- 要求只返回 JSON，不输出 Markdown。
- 要求忽略身份证、手机号、支付金额、银行卡号等敏感信息。
- 对缺失日期、时间、地点的结果加 `warnings`，并把 `confidence` 降为 `low` 或 `medium`。
- 对飞机、高铁、酒店做优先识别：
  - 飞机：航班号、起飞机场、到达机场、起飞时间、到达时间。
  - 高铁：车次、出发站、到达站、发车时间、到达时间。
  - 酒店：酒店名、地址、入住日期、离店日期。

## 候选事件映射

交通订单：

- `eventType`: `transport`
- `meta.icon`: `plane`、`train`、`bus`、`car`
- `meta.transportMode`: `flight`、`train`、`bus`、`car`
- `title`: `航班/车次 + 出发地 → 到达地`
- `startAt`: 出发时间
- `endAt`: 到达时间
- `locationName`: 出发机场或车站
- `note`: 到达地、订单摘要、需要人工确认的信息

酒店订单：

- `eventType`: `stay`
- `meta.icon`: `hotel`
- `meta.allDay`: `true`
- `title`: `入住 + 酒店名`
- `startAt`: 入住日期 00:00
- `endAt`: 离店日期 00:00
- `locationName`: 酒店名
- `address`: 酒店地址
- `note`: 房型、入住人等非敏感摘要

无法分类但可用的信息：

- `eventType`: `reminder`
- `meta.icon`: `ticket` 或 `clock`
- `confidence`: `low`
- 前端默认要求用户编辑后才能保存

## 前端设计

修改 `miniapp/src/pages/edit/index.vue`：

- 在“每日行程”标题区域增加 `AI导入` 小按钮。
- 新增 `aiImportOpen`、`aiImportLoading`、`aiImportCandidates` 状态。
- 使用 `uni.chooseImage` 选择截图。
- 使用 `uni.uploadFile` 上传图片。小程序多图兼容策略：
  - v1 前端逐张调用识别接口，再在客户端合并候选事件。
  - 后端接口同时支持一张或多张图片，为后续 H5/App 多文件上传留空间。
- 识别结果用列表弹层展示。
- 单条候选编辑复用当前事件编辑弹层的字段和校验逻辑。
- 保存时调用 `POST /trips/{tripId}/ai/import-events`，成功后刷新 `tripEventApi.list(tripId)`。

新增 `miniapp/src/services/ai-import.ts`：

- `extractTripEvents(tripId, filePaths)`
- `importTripEvents(tripId, events)`
- 类型定义 `AiTripEventCandidate`、`AiExtractEventsResponse`

## 错误处理

- 未保存行程：提示“请先保存行程后再导入”。
- 无图片：不发请求。
- 图片过大：前端提示，后端返回 413。
- AI 未识别到事件：提示“未识别到可导入的行程信息”。
- AI 返回非法 JSON：后端返回 502，提示“识别结果异常，请重试”。
- AI 超时：后端返回 504，提示“识别超时，请稍后重试”。
- 候选事件缺少 `startAt`：前端标记“需编辑”，禁止直接保存。
- `endAt < startAt`：前端和后端都拒绝保存。

## 安全与隐私

- 图片不持久化。
- 不在日志中记录 base64 图片、AI 原始请求体或完整订单内容。
- API key 只存在后端环境变量，不进入小程序。
- 所有接口复用现有登录鉴权和行程访问权限判断。
- 后端只允许图片 MIME 类型，不接受 PDF、HTML 或任意文件。
- 模型 prompt 明确忽略身份证、手机号、支付、银行卡等敏感信息。
- sub2api 后台和平台 key 仍由服务器管理，前端只调用 CandyTravel 后端。

## 测试策略

后端单元测试：

- `ai_trip_event_extractor` 能把合法 AI JSON 转成候选事件。
- 非 JSON 或 schema 不匹配时返回明确错误。
- 缺少日期或时间的候选项带 `warnings`。
- 敏感字段不会进入 `note` 或 `meta`。

后端接口测试：

- 未登录请求返回 401。
- 无访问权限的行程返回 404。
- 非图片上传返回 400。
- 超过大小限制返回 413。
- 导入确认接口创建 `source=ai_extracted` 的事件。
- 导入确认接口拒绝无效时间区间。

前端手动验证：

- 已保存行程可以点击 `AI导入`。
- 未保存行程提示先保存。
- 上传一张飞机订单截图后能看到候选航班事件。
- 用户编辑候选事件后保存，事件出现在每日行程。
- 移除候选项后不会保存。
- 网络失败时不会产生事件。

## 已决延期项

- v1 不做重复事件自动去重；如果识别出的事件时间和标题与现有事件接近，只在确认列表中提示“可能重复”。
- v1 不支持 PDF 订单；如果后续需要，可增加 PDF 转图片或文档解析流程。
- v1 不做后台任务；如果识别耗时明显影响体验，再引入异步 job。
