# 行程地图视图设计

## 背景

CandyTravel 已经有行程事件、日程编辑和清单能力。用户在规划多地点行程时，需要快速看到每天或整段行程的空间分布，判断当前时间顺序是否绕路。第一版只做按现有时间顺序的地图总览，不做自动路线优化。

## 目标

- 在行程页增加「日程 / 地图 / 清单」切换。
- 地图视图展示有坐标的行程事件，并按 `startAt + sortOrder` 顺序用直线连接。
- 事件表单保留地点输入框，并在旁边增加「地图选择」按钮。
- 用户通过地图选择地点后，事件保存 `locationName`、`address`、`latitude`、`longitude`。
- 用户手动修改地点展示文本时不清空坐标；只有重新地图选择才更新坐标。
- 地图视图对缺坐标事件给出补全提示。

## 非目标

- 不做真实步行、驾车、公交路线规划。
- 不做最短路径或游玩顺序自动推荐。
- 不做营业时间、预约时间、交通耗时校验。
- 不做后端地址解析和自动 geocoding。
- 不做跨地图坐标系转换；第一版使用小程序地图选择返回的坐标。

## 用户流程

### 选择地点

1. 用户打开行程事件表单。
2. 在「地点」输入框旁点击「地图选择」。
3. 小程序打开地图地点选择页。
4. 用户搜索并选择 POI。
5. 前端回填地点名和地址，并保存经纬度。
6. 用户可以继续编辑地点展示文本，坐标保持不变。
7. 用户再次点击「地图选择」并选择新 POI 时，坐标随新 POI 更新。

### 查看地图

1. 用户进入行程页。
2. 点击顶部「地图」tab。
3. 地图显示有坐标事件的 marker。
4. marker 按当前行程时间顺序编号。
5. 地图用直线连接这些 marker。
6. 地图下方列出缺坐标事件，引导用户回到事件表单使用「地图选择」补全位置。

## 页面结构

```text
行程页
┌────────────────────────────┐
│ 京都周末游                  │
│ 日程   地图   清单           │
├────────────────────────────┤
│                            │
│        <map>               │
│   ① ───── ② ───── ③        │
│                            │
├────────────────────────────┤
│ 未上地图                    │
│ 10:00 湖边咖啡馆  选择地图地点 │
└────────────────────────────┘
```

```text
事件表单
┌────────────────────────────┐
│ 地点                        │
│ [酒店                  ] [地图选择] │
│ 已绑定地图位置：全季酒店杭州西湖店 │
└────────────────────────────┘
```

## 数据模型

`trip_events` 增加两个可空字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `latitude` | DOUBLE PRECISION | 小程序地图地点选择返回的纬度 |
| `longitude` | DOUBLE PRECISION | 小程序地图地点选择返回的经度 |

约束：

- `latitude` 和 `longitude` 必须同时为空或同时有值。
- `latitude` 范围为 `-90` 到 `90`。
- `longitude` 范围为 `-180` 到 `180`。

前端 `TripEvent`、`TripEventCreatePayload`、`TripEventPatchPayload` 同步增加：

```ts
latitude?: number | null
longitude?: number | null
```

## API 行为

- `GET /api/v1/trips/{tripId}/events` 返回 `latitude`、`longitude`。
- `POST /api/v1/trips/{tripId}/events` 接收 `latitude`、`longitude`。
- `PATCH /api/v1/events/{eventId}` 接收 `latitude`、`longitude`。
- 如果请求只修改 `locationName` 或 `address`，后端不改动已有坐标。
- 如果请求显式传入新的 `latitude` 和 `longitude`，后端更新坐标。
- 如果后续需要支持移除坐标，可以允许前端显式传 `latitude: null, longitude: null`；第一版 UI 不提供独立入口。

## 前端组件

### 地图 tab

地图 tab 从当前行程事件里派生：

- `mappableEvents`: 同时有 `latitude` 和 `longitude` 的事件。
- `missingLocationEvents`: 有地点文本但缺少坐标的事件，或完全没有地点的活动事件。
- `markers`: 由 `mappableEvents` 转成 map marker，标题使用事件展示地点或标题。
- `polyline`: 按 `mappableEvents` 顺序生成折线点。
- `includePoints`: 使用所有 marker 坐标，让地图自动显示完整范围。

空状态：

- 没有任何坐标事件时，显示「还没有可上地图的地点」。
- 有缺坐标事件时，显示「使用地图选择地点后会出现在路线图中」。

### 地点表单

- 地点输入框继续编辑 `locationName`。
- 地址字段可继续作为后端字段保存，第一版不需要额外暴露独立输入。
- 「地图选择」调用 `uni.chooseLocation`。
- 选择成功后：
  - `locationName = result.name || locationName`
  - `address = result.address || address`
  - `latitude = result.latitude`
  - `longitude = result.longitude`
- 如果用户取消地图选择，不改变表单。
- 如果事件已有坐标，表单显示「已绑定地图位置」提示。

## 数据流

```text
用户地图选择
  → uni.chooseLocation
  → 表单写入 locationName/address/latitude/longitude
  → POST/PATCH 保存事件
  → 行程事件列表刷新
  → 地图 tab 派生 markers/polyline
```

## 错误处理

- 用户取消地图选择：静默返回表单。
- 地图选择 API 失败：toast 提示「暂时无法打开地图选择」。
- 保存坐标失败：保留表单内容，提示保存失败。
- 地图 tab 事件坐标不完整：该事件不进地图，进入缺坐标提示列表。

## 测试计划

后端：

- 迁移新增 `latitude`、`longitude` 字段。
- 创建事件时可保存坐标。
- 更新地点文本时不清空坐标。
- 显式更新坐标时坐标变化。
- 非法经纬度返回校验错误。

前端：

- `TripEvent` 类型包含坐标字段。
- 地图选择成功后表单写入地点、地址和坐标。
- 手动修改地点文本不改变坐标。
- 地图 tab 只展示有完整坐标的事件。
- polyline 顺序与 `startAt + sortOrder` 一致。
- 缺坐标事件出现在提示列表。

## 验收标准

- 用户能在事件表单中通过「地图选择」绑定坐标。
- 用户能手动改地点展示名，原坐标仍保留。
- 地图 tab 能看到有坐标事件的编号 marker 和连线。
- 无坐标事件不会破坏地图展示，并能被明确提示。
- 第一版不会给用户造成“已自动优化路线”的误解。
