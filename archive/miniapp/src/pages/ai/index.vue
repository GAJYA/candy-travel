<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiRequestError, aiImportApi, type AiImportJob } from "../../services/api";

type DraftConfidence = "high" | "medium" | "low";

type DraftField = {
  value: string;
  confidence: DraftConfidence;
};

type DraftPackingItem = {
  id: string;
  label: string;
  checked: boolean;
  category: string;
};

type DraftExtraction = {
  tripTitle: DraftField;
  travelDate: DraftField;
  departureTime: DraftField;
  arrivalTime: DraftField;
  origin: DraftField;
  destination: DraftField;
  reference: DraftField;
  hotel: DraftField;
  note: DraftField;
  packingItems: DraftPackingItem[];
  warnings: string[];
};

const sampleInput = `5月18日 北京飞上海，航班 MU5101，09:30 起飞，11:45 落地。
入住南京西路附近的静安嘉里酒店两晚。
记得带身份证、充电宝，周日晚上去外滩。`;

const inputText = ref(sampleInput);
const isExtracting = ref(false);
const isSaving = ref(false);
const draft = ref<DraftExtraction | null>(null);
const currentJobId = ref<string | null>(null);
const saveMessage = ref("");
const errorMessage = ref("");

const confidenceLabel: Record<DraftConfidence, string> = {
  high: "高置信",
  medium: "待确认",
  low: "低置信",
};

const sourceSummary = computed(() => {
  const normalized = inputText.value.trim().replace(/\s+/g, " ");
  if (!normalized) return "还没有输入待提取的文本";
  return normalized.length > 80 ? `${normalized.slice(0, 80)}...` : normalized;
});

const formatDateLabel = (value: string) => {
  if (!value) return "待补充";
  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) return "待补充";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    weekday: "long",
  }).format(date);
};

const extractTimeFromIso = (isoString: string): DraftField => {
  if (!isoString) return { value: "", confidence: "low" };
  const timePart = isoString.length >= 16 ? isoString.slice(11, 16) : "";
  return { value: timePart, confidence: timePart ? "high" : "low" };
};

const createHintId = (index: number) => `hint_${index}_${Math.random().toString(36).slice(2, 8)}`;

const mapJobToDraft = (job: AiImportJob): DraftExtraction => {
  const payload = job.extractedPayloadJson;
  const firstItem = payload.items[0];

  return {
    tripTitle: { value: payload.tripDraft.title.value, confidence: payload.tripDraft.title.confidence },
    travelDate: { value: payload.tripDraft.startDate.value, confidence: payload.tripDraft.startDate.confidence },
    departureTime: firstItem ? extractTimeFromIso(firstItem.startAt) : { value: "", confidence: "low" },
    arrivalTime: firstItem?.endAt ? extractTimeFromIso(firstItem.endAt) : { value: "", confidence: "low" },
    origin: { value: payload.tripDraft.originCity.value, confidence: payload.tripDraft.originCity.confidence },
    destination: { value: payload.tripDraft.destinationCity.value, confidence: payload.tripDraft.destinationCity.confidence },
    reference: firstItem ? { value: firstItem.referenceCode.value, confidence: firstItem.referenceCode.confidence } : { value: "", confidence: "low" },
    hotel: { value: payload.tripDraft.hotelName.value, confidence: payload.tripDraft.hotelName.confidence },
    note: { value: payload.tripDraft.note.value, confidence: payload.tripDraft.note.confidence },
    packingItems: payload.packingHints.map((hint, index) => ({
      id: createHintId(index),
      label: hint.label,
      checked: hint.checked,
      category: hint.category,
    })),
    warnings: payload.warnings,
  };
};

const handleExtract = async () => {
  if (!inputText.value.trim()) return;

  saveMessage.value = "";
  errorMessage.value = "";
  isExtracting.value = true;

  try {
    const response = await aiImportApi.createJob({ inputType: "text", rawText: inputText.value });
    currentJobId.value = response.job.id;
    draft.value = mapJobToDraft(response.job);
  } catch (err) {
    errorMessage.value = err instanceof ApiRequestError ? err.message : "AI 提取失败，请稍后重试";
  } finally {
    isExtracting.value = false;
  }
};

const resetDraft = () => {
  draft.value = null;
  currentJobId.value = null;
  saveMessage.value = "";
  errorMessage.value = "";
};

const togglePackingItem = (itemId: string) => {
  if (!draft.value) return;
  draft.value.packingItems = draft.value.packingItems.map((item) =>
    item.id === itemId ? { ...item, checked: !item.checked } : item,
  );
};

const handleSave = async () => {
  if (!draft.value || !currentJobId.value) return;

  isSaving.value = true;
  errorMessage.value = "";

  try {
    await aiImportApi.commitJob(currentJobId.value);
    saveMessage.value = `已保存：${draft.value.tripTitle.value}`;
    uni.showToast({ title: "已保存", icon: "success" });
  } catch (err) {
    errorMessage.value = err instanceof ApiRequestError ? err.message : "保存失败，请稍后重试";
    uni.showToast({ title: "保存失败", icon: "error" });
  } finally {
    isSaving.value = false;
  }
};
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="title">AI 文本提取助手</text>
      <text class="desc">粘贴行程文本，AI 自动解析结构化草稿，确认后一键存入行程。</text>
    </view>

    <view class="panel">
      <text class="label">待提取文本</text>
      <textarea v-model="inputText" class="textarea" placeholder="粘贴航班、酒店或活动信息..." />
      <view class="summary">
        <text class="summary-label">输入摘要</text>
        <text class="summary-text">{{ sourceSummary }}</text>
      </view>
      <view v-if="errorMessage && !draft" class="error-box">
        <text class="error-text">{{ errorMessage }}</text>
      </view>
      <button class="button primary" :disabled="isExtracting || !inputText.trim()" @tap="handleExtract">
        {{ isExtracting ? "正在提取..." : "开始提取" }}
      </button>
    </view>

    <view v-if="draft" class="panel">
      <view class="section-head">
        <text class="label">提取结果确认</text>
        <text class="badge">待确认</text>
      </view>

      <view v-if="draft.warnings.length" class="warning-box">
        <text class="warning-title">需要人工确认</text>
        <text v-for="warning in draft.warnings" :key="warning" class="warning-item">- {{ warning }}</text>
      </view>

      <view class="field">
        <text class="field-label">行程标题</text>
        <input v-model="draft.tripTitle.value" class="input" type="text" />
        <text class="confidence">{{ confidenceLabel[draft.tripTitle.confidence] }}</text>
      </view>

      <view class="field">
        <text class="field-label">日期</text>
        <picker mode="date" :value="draft.travelDate.value" @change="draft.travelDate.value = $event.detail.value">
          <view class="picker">{{ formatDateLabel(draft.travelDate.value) }}</view>
        </picker>
        <text class="confidence">{{ confidenceLabel[draft.travelDate.confidence] }}</text>
      </view>

      <view class="field-grid">
        <view class="field">
          <text class="field-label">出发时间</text>
          <picker mode="time" :value="draft.departureTime.value" @change="draft.departureTime.value = $event.detail.value">
            <view class="picker">{{ draft.departureTime.value || "待补充" }}</view>
          </picker>
        </view>
        <view class="field">
          <text class="field-label">到达时间</text>
          <picker mode="time" :value="draft.arrivalTime.value" @change="draft.arrivalTime.value = $event.detail.value">
            <view class="picker">{{ draft.arrivalTime.value || "待补充" }}</view>
          </picker>
        </view>
      </view>

      <view class="field-grid">
        <view class="field">
          <text class="field-label">出发地</text>
          <input v-model="draft.origin.value" class="input" type="text" />
        </view>
        <view class="field">
          <text class="field-label">目的地</text>
          <input v-model="draft.destination.value" class="input" type="text" />
        </view>
      </view>

      <view class="field">
        <text class="field-label">航班号 / 车次</text>
        <input v-model="draft.reference.value" class="input" type="text" />
        <text class="confidence">{{ confidenceLabel[draft.reference.confidence] }}</text>
      </view>

      <view class="field">
        <text class="field-label">酒店 / 落脚点</text>
        <input v-model="draft.hotel.value" class="input" type="text" placeholder="可留空，后续继续补充" />
      </view>

      <view class="field">
        <text class="field-label">旅行备注</text>
        <textarea v-model="draft.note.value" class="textarea note" placeholder="补充重点活动或提醒..." />
      </view>

      <view class="field">
        <text class="field-label">准备清单</text>
        <view class="packing-list">
          <view
            v-for="item in draft.packingItems"
            :key="item.id"
            class="packing-item"
            :class="{'packing-item--checked': item.checked}"
            @tap="togglePackingItem(item.id)"
          >
            <text class="packing-mark">{{ item.checked ? "✓" : "○" }}</text>
            <text class="packing-text">{{ item.label }}</text>
          </view>
        </view>
      </view>

      <view v-if="errorMessage" class="error-box">
        <text class="error-text">{{ errorMessage }}</text>
      </view>

      <view v-if="saveMessage" class="success-box">
        <text class="success-text">{{ saveMessage }}</text>
      </view>

      <view class="actions">
        <button class="button secondary" @tap="resetDraft">放弃</button>
        <button class="button primary" :disabled="isSaving || !!saveMessage" @tap="handleSave">
          {{ isSaving ? "保存中..." : "确认并保存" }}
        </button>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 32rpx;
  background: #fff7fb;
}

.hero,
.panel {
  padding: 28rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.06);
}

.panel {
  margin-top: 24rpx;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #111827;
}

.desc {
  display: block;
  margin-top: 12rpx;
  font-size: 28rpx;
  line-height: 1.7;
  color: #6b7280;
}

.label,
.field-label,
.summary-label,
.warning-title {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: #1f2937;
}

.textarea,
.input,
.picker {
  width: 100%;
  margin-top: 16rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: #fff4fa;
  font-size: 28rpx;
  color: #111827;
}

.textarea {
  min-height: 240rpx;
}

.note {
  min-height: 160rpx;
}

.summary {
  margin-top: 20rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: #fff8fc;
}

.summary-text,
.warning-item,
.success-text,
.error-text,
.confidence {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: #6b7280;
}

.warning-box,
.success-box,
.error-box {
  margin-top: 20rpx;
  padding: 20rpx;
  border-radius: 24rpx;
}

.warning-box {
  background: #fff7ed;
}

.success-box {
  background: #ecfdf5;
}

.error-box {
  background: #fef2f2;
}

.error-text {
  color: #dc2626;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.badge {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #dbeafe;
  font-size: 22rpx;
  font-weight: 700;
  color: #2563eb;
}

.field,
.field-grid,
.packing-list,
.actions {
  margin-top: 24rpx;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
}

.packing-item {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 16rpx;
  padding: 20rpx 24rpx;
  border-radius: 999rpx;
  background: #fff8fc;
}

.packing-item--checked {
  background: #eefbf4;
}

.packing-mark {
  font-size: 28rpx;
  color: #e11d8b;
}

.packing-text {
  font-size: 26rpx;
  color: #1f2937;
}

.button {
  margin-top: 24rpx;
  border-radius: 999rpx;
  font-size: 28rpx;
}

.button::after {
  border: none;
}

.primary {
  background: linear-gradient(135deg, #ff6cab, #7f7fd5);
  color: #ffffff;
}

.secondary {
  background: #fce7f3;
  color: #9d174d;
}

.actions {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 20rpx;
}
</style>
