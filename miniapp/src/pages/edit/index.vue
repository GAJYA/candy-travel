<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { ApiRequestError, tripApi, type TripListResponse, type TripRecord } from "../../services/api";

type TransportMode = "flight" | "train" | "bus" | "car";
type PackingCategory = "document" | "electronics" | "clothing" | "medicine" | "food" | "other";
type TripOption = TripListResponse["items"][number];

const tripOptions = ref<TripOption[]>([]);
const currentTrip = ref<TripRecord | null>(null);
const selectedTripId = ref("");
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");

const tripForm = reactive({
  title: "",
  destinationCity: "",
  originCity: "",
  hotelName: "",
  note: "",
  primaryTransportMode: "flight" as TransportMode,
});

const newPackingLabel = reactive({
  value: "",
});

const packingItems = computed(() => currentTrip.value?.packingItems ?? []);

const syncForm = () => {
  if (!currentTrip.value) return;
  tripForm.title = currentTrip.value.title;
  tripForm.destinationCity = currentTrip.value.destinationCity;
  tripForm.originCity = currentTrip.value.originCity;
  tripForm.hotelName = currentTrip.value.hotelName;
  tripForm.note = currentTrip.value.note;
  tripForm.primaryTransportMode = currentTrip.value.primaryTransportMode as TransportMode;
};

const loadTripOptions = async (preferredTripId?: string) => {
  const response = await tripApi.list();
  tripOptions.value = response.items;

  if (!selectedTripId.value) {
    selectedTripId.value = response.items.find((trip) => trip.id === preferredTripId)?.id ?? response.items[0]?.id ?? "";
  }
};

const loadTrip = async (tripId = selectedTripId.value) => {
  if (!tripId) return;

  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await tripApi.get(tripId);
    selectedTripId.value = tripId;
    currentTrip.value = response.item;
    syncForm();
  } catch (error) {
    errorMessage.value = error instanceof ApiRequestError ? error.message : "计划详情加载失败";
  } finally {
    loading.value = false;
  }
};

const saveTrip = async () => {
  if (!currentTrip.value) return;

  saving.value = true;
  try {
    const response = await tripApi.update(currentTrip.value.id, {
      title: tripForm.title,
      destinationCity: tripForm.destinationCity,
      originCity: tripForm.originCity,
      hotelName: tripForm.hotelName,
      note: tripForm.note,
      primaryTransportMode: tripForm.primaryTransportMode,
    });
    currentTrip.value = response.item;
    syncForm();
    uni.showToast({ title: "计划已保存", icon: "success" });
  } catch (error) {
    uni.showToast({ title: error instanceof ApiRequestError ? error.message : "保存失败", icon: "none" });
  } finally {
    saving.value = false;
  }
};

const addPackingItem = async () => {
  if (!currentTrip.value || !newPackingLabel.value) return;

  saving.value = true;
  try {
    const response = await tripApi.createPackingItem(currentTrip.value.id, {
      label: newPackingLabel.value,
      checked: false,
      category: "other" as PackingCategory,
      source: "manual",
      sortOrder: packingItems.value.length,
    });
    currentTrip.value = response.item;
    newPackingLabel.value = "";
  } catch (error) {
    uni.showToast({ title: error instanceof ApiRequestError ? error.message : "新增清单失败", icon: "none" });
  } finally {
    saving.value = false;
  }
};

const togglePacking = async (itemId: string, checked: boolean) => {
  saving.value = true;
  try {
    const response = await tripApi.updatePackingItem(itemId, { checked: !checked });
    currentTrip.value = response.item;
  } catch (error) {
    uni.showToast({ title: error instanceof ApiRequestError ? error.message : "更新清单失败", icon: "none" });
  } finally {
    saving.value = false;
  }
};

const deletePacking = async (itemId: string) => {
  saving.value = true;
  try {
    const response = await tripApi.deletePackingItem(itemId);
    currentTrip.value = response.item;
  } catch (error) {
    uni.showToast({ title: error instanceof ApiRequestError ? error.message : "删除清单失败", icon: "none" });
  } finally {
    saving.value = false;
  }
};

const handleTripChange = (event: { detail: { value: number | string } }) => {
  const nextTrip = tripOptions.value[Number(event.detail.value)];
  if (!nextTrip) return;
  void loadTrip(nextTrip.id);
};

watch(currentTrip, () => {
  syncForm();
});

onLoad(async (query) => {
  const tripId = typeof query?.tripId === "string" ? query.tripId : "";
  await loadTripOptions(tripId);
  if (tripId) {
    selectedTripId.value = tripId;
  }
  await loadTrip(selectedTripId.value || tripId);
});

onShow(() => {
  if (selectedTripId.value) {
    void loadTrip(selectedTripId.value);
  }
});
</script>

<template>
  <view class="page">
    <view class="header">
      <text class="title">{{ currentTrip ? currentTrip.title : "计划编辑" }}</text>
      <text class="desc">维护 Trip 基础字段、交通方式和打包清单。</text>
    </view>

    <view class="panel">
      <text class="label">当前行程</text>
      <picker :range="tripOptions.map((trip) => trip.title)" @change="handleTripChange">
        <view class="input picker">{{ currentTrip ? currentTrip.title : "请选择行程" }}</view>
      </picker>
      <text v-if="errorMessage" class="status-text status-text--error">{{ errorMessage }}</text>
      <text v-else-if="loading" class="status-text">正在读取服务端计划详情…</text>
    </view>

    <view class="panel">
      <text class="label">行程标题</text>
      <input v-model="tripForm.title" class="input" placeholder="例如：京都樱花之旅" />

      <text class="label">出发城市</text>
      <input v-model="tripForm.originCity" class="input" placeholder="输入出发城市" />

      <text class="label">目的地</text>
      <input v-model="tripForm.destinationCity" class="input" placeholder="输入目的地城市" />

      <text class="label">交通方式</text>
      <picker :range="['flight', 'train', 'bus', 'car']" @change="tripForm.primaryTransportMode = ['flight', 'train', 'bus', 'car'][$event.detail.value] as TransportMode">
        <view class="input picker">{{ tripForm.primaryTransportMode }}</view>
      </picker>

      <text class="label">酒店</text>
      <input v-model="tripForm.hotelName" class="input" placeholder="输入酒店信息" />

      <text class="label">旅行笔记</text>
      <textarea v-model="tripForm.note" class="textarea" placeholder="补充提醒、出行备注..." />

      <button class="button" :loading="saving" @tap="saveTrip">保存计划</button>
    </view>

    <view class="panel">
      <text class="title title--small">打包清单</text>
      <view class="packing-list">
        <view v-for="item in packingItems" :key="item.id" class="packing-item">
          <label class="packing-check">
            <checkbox :checked="item.checked" @tap="togglePacking(item.id, item.checked)" />
            <text class="packing-label">{{ item.label }}</text>
          </label>
          <button class="delete-link" @tap="deletePacking(item.id)">删除</button>
        </view>
      </view>

      <input v-model="newPackingLabel.value" class="input" placeholder="新增清单项" />
      <button class="button button--ghost" :loading="saving" @tap="addPackingItem">添加清单项</button>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 32rpx;
}

.header,
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
  font-size: 36rpx;
  font-weight: 700;
  color: #111827;
}

.desc,
.label {
  display: block;
  margin-top: 12rpx;
  font-size: 28rpx;
  color: #6b7280;
}

.status-text {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.status-text--error {
  color: #be123c;
}

.input {
  width: 100%;
  margin-top: 12rpx;
  padding: 22rpx 24rpx;
  border-radius: 22rpx;
  background: #fff4fa;
}

.picker,
.textarea {
  width: 100%;
}

.textarea {
  margin-top: 12rpx;
  min-height: 140rpx;
  padding: 22rpx 24rpx;
  border-radius: 22rpx;
  background: #fff4fa;
}

.button {
  margin-top: 28rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #ff6cab, #7f7fd5);
  color: #ffffff;
}

.button--ghost {
  background: #fce7f3;
  color: #be185d;
}

.title--small {
  font-size: 32rpx;
}

.packing-list {
  margin-top: 16rpx;
}

.packing-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 0;
  border-bottom: 1px solid #f3e8ff;
}

.packing-check {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.packing-label {
  font-size: 26rpx;
  color: #111827;
}

.delete-link {
  padding: 0;
  background: transparent;
  color: #be185d;
  font-size: 24rpx;
  line-height: 1.5;
}
</style>
