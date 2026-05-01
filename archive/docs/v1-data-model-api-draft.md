# CandyTravel V1 数据模型与 API 契约初稿

## 目标

基于当前原型，V1 先聚焦四条真实链路：

1. 首页看行程概览和 upcoming trips
2. 日历页按天查看和维护行程
3. AI 页把文本或票据内容提取成结构化行程草稿
4. 编辑页维护目的地、交通、酒店、笔记和打包清单

V1 不做 OTA 式复杂交易建模，先围绕个人旅行计划管理收敛。

## 核心实体

### users

- `id`
- `nickname`
- `avatar_url`
- `locale`
- `timezone`
- `created_at`
- `updated_at`

### trips

- `id`
- `user_id`
- `title`
- `cover_image_url`
- `status` enum: `draft | planning | confirmed | completed | archived`
- `start_date`
- `end_date`
- `origin_city`
- `destination_city`
- `primary_transport_mode` enum: `flight | train | bus | car`
- `hotel_name`
- `note`
- `countdown_anchor_at`
- `created_via` enum: `manual | ai_import`
- `created_at`
- `updated_at`

### trip_days

- `id`
- `trip_id`
- `date`
- `summary`
- `hint`
- `highlight_tag`
- `sort_order`
- `created_at`
- `updated_at`

### trip_events

- `id`
- `trip_id`
- `trip_day_id` nullable
- `event_type` enum: `transport | stay | activity | reminder`
- `title`
- `description`
- `start_at`
- `end_at` nullable
- `location_name` nullable
- `address` nullable
- `transport_mode` nullable enum: `flight | train | bus | car`
- `reference_code` nullable
- `source` enum: `manual | ai_extracted`
- `source_job_id` nullable
- `status` enum: `draft | confirmed | canceled`
- `meta_json` jsonb
- `created_at`
- `updated_at`

### packing_items

- `id`
- `trip_id`
- `label`
- `checked`
- `category` enum: `document | electronics | clothing | medicine | food | other`
- `source` enum: `manual | ai_generated`
- `sort_order`
- `created_at`
- `updated_at`

### ai_import_jobs

- `id`
- `user_id`
- `trip_id` nullable
- `input_type` enum: `text | image`
- `raw_text` nullable
- `file_url` nullable
- `status` enum: `pending | processing | parsed | committed | failed`
- `error_message` nullable
- `extracted_payload_json` jsonb
- `created_at`
- `updated_at`

## 建模说明

- `trip` 是聚合根，保证首页、日历、编辑页都围绕同一主对象工作。
- `trip_days` 保留当天的摘要、提示和高亮标签，不强依赖实时计算。
- `trip_events` 统一承载交通、住宿、活动和提醒，先满足 MVP，避免早拆专表。
- `ai_import_jobs` 采用 job + commit 两段式，先提取、再确认、后入库。

## 推荐 API

### 首页

`GET /api/v1/home`

### 行程列表与详情

- `GET /api/v1/trips`
- `POST /api/v1/trips`
- `GET /api/v1/trips/:tripId`
- `PATCH /api/v1/trips/:tripId`

### 日历与按天详情

- `GET /api/v1/trips/:tripId/calendar?month=YYYY-MM`
- `GET /api/v1/trips/:tripId/days/:date`

### 行程事件

- `POST /api/v1/trips/:tripId/events`
- `PATCH /api/v1/events/:eventId`
- `DELETE /api/v1/events/:eventId`

### 打包清单

- `GET /api/v1/trips/:tripId/packing-items`
- `POST /api/v1/trips/:tripId/packing-items`
- `PATCH /api/v1/packing-items/:itemId`
- `DELETE /api/v1/packing-items/:itemId`

### AI 导入

- `POST /api/v1/ai-import-jobs`
- `GET /api/v1/ai-import-jobs/:jobId`
- `POST /api/v1/ai-import-jobs/:jobId/commit`

## 约束建议

- `trips.start_date <= trips.end_date`
- `trip_days.date` 必须落在 trip 的日期范围内
- `trip_events.trip_id` 与 `trip_day.trip_id` 必须一致
- 同一 trip 下 `packing_items.label` 建议唯一
- `ai_import_jobs` 一旦 commit 成功，需要幂等保护，避免重复入库
