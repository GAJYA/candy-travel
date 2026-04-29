<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";
import { ApiRequestError, tripApi, type TripCalendarResponse, type TripDayRecord, type TripEventRecord, type TripListResponse } from "../../services/api";

type EventTypeOption = "activity" | "transport" | "stay" | "reminder";
type TripOption = TripListResponse["items"][number];
type CalendarTrip = TripCalendarResponse["trip"] & {
  days: TripDayRecord[];
  events: TripEventRecord[];
};

const tripOptions = ref<TripOption[]>([]);
const currentTrip = ref<CalendarTrip | null>(null);
const selectedTripId = ref("");
const selectedDate = ref("");
const loading = ref(false);
const saving = ref(false);
const errorMessage = ref("");

const dayForm = reactive({
  summary: "",
  hint: "",
  highlightTag: "",
});

const eventForm = reactive({
  title: "",
  description: "",
  time: "09:30",
  eventType: "activity" as EventTypeOption,
});

const eventTypeOptions: EventTypeOption[] = ["activity", "transport", "stay", "reminder"];

const formatDateOnly = (date: Date) => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
};

const buildDateRange = (startDate: string, endDate: string) => {
  const days: string[] = [];
  const cursor = new Date(`${startDate}T00:00:00`);
  const limit = new Date(`${endDate}T00:00:00`);

  while (cursor.getTime() <= limit.getTime()) {
    days.push(formatDateOnly(cursor));
    cursor.setDate(cursor.getDate() + 1);
  }

  return days;
};

const availableDates = computed(() => {
  if (!currentTrip.value) return [];
  return buildDateRange(currentTrip.value.startDate, currentTrip.value.endDate);
});

const dateChips = computed(() =>
  availableDates.value.map((date) => {
    const day = currentTrip.value?.days.find((item) => item.date === date);
    return {
      date,
      highlightTag: day?.highlightTag || "未安排",
    };
  }),
);

const selectedDay = computed(() => currentTrip.value?.days.find((day) => day.date === selectedDate.value) ?? null);
const dayEvents = computed(() => (currentTrip.value?.events ?? []).filter((event) => event.startAt.slice(0, 10) === selectedDate.value));

const syncDayForm = () => {
  dayForm.summary = selectedDay.value?.summary ?? "";
  dayForm.hint = selectedDay.value?.hint ?? "";
  dayForm.highlightTag = selectedDay.value?.highlightTag ?? "";
};

const applyCalendarResponse = (response: TripCalendarResponse, preferredDate?: string) => {
  currentTrip.value = {
    ...response.trip,
    days: response.days,
    events: response.events,
  };

  const nextDate =
    preferredDate && availableDates.value.includes(preferredDate)
      ? preferredDate
      : response.days[0]?.date || response.trip.startDate;
  selectedDate.value = nextDate;
  syncDayForm();
};

const loadTripOptions = async (preferredTripId?: string) => {
  const response = await tripApi.list();
  tripOptions.value = response.items;

  const fallbackTripId = response.items.find((trip) => trip.id === preferredTripId)?.id ?? response.items[0]?.id ?? "";
  if (fallbackTripId && !selectedTripId.value) {
    selectedTripId.value = fallbackTripId;
  }
};

const loadCalendar = async (tripId = selectedTripId.value, preferredDate?: string) => {
  if (!tripId) return;

  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await tripApi.getCalendar(tripId);
    selectedTripId.value = tripId;
    applyCalendarResponse(response, preferredDate);
  } catch (error) {
    errorMessage.value = error instanceof ApiRequestError ? error.message : "日历数据加载失败";
  } finally {
    loading.value = false;
  }
};

const ensureDay = async () => {
  if (!currentTrip.value || !selectedDate.value) return selectedDay.value;
  if (selectedDay.value) return selectedDay.value;

  const response = await tripApi.createDay(currentTrip.value.id, {
    date: selectedDate.value,
    summary: dayForm.summary || "今天还没有安排行程",
    hint: dayForm.hint || "可以继续补充交通、活动或住宿安排。",
    highlightTag: dayForm.highlightTag || "空闲",
    sortOrder: currentTrip.value.days.length,
  });

  const nextTrip = response.item;
  currentTrip.value = {
    id: nextTrip.id,
    title: nextTrip.title,
    status: nextTrip.status,
    startDate: nextTrip.startDate,
    endDate: nextTrip.endDate,
    destinationCity: nextTrip.destinationCity,
    days: nextTrip.days,
    events: nextTrip.events,
  };
  return currentTrip.value.days.find((day) => day.date === selectedDate.value) ?? null;
};

const selectDate = (date: string) => {
  selectedDate.value = date;
  syncDayForm();
};

const handleTripChange = (event: { detail: { value: number | string } }) => {
  const nextTrip = tripOptions.value[Number(event.detail.value)];
  if (!nextTrip) return;
  void loadCalendar(nextTrip.id);
};

const handleDateChange = (event: { detail: { value: string } }) => {
  selectDate(event.detail.value);
};

const saveDay = async () => {
  if (!currentTrip.value || !selectedDate.value) return;

  saving.value = true;
  try {
    if (selectedDay.value) {
      await tripApi.updateDay(currentTrip.value.id, selectedDay.value.id, {
        summary: dayForm.summary || "今天还没有安排行程",
        hint: dayForm.hint || "可以继续补充交通、活动或住宿安排。",
        highlightTag: dayForm.highlightTag || "空闲",
      });
    } else {
      await tripApi.createDay(currentTrip.value.id, {
        date: selectedDate.value,
        summary: dayForm.summary || "今天还没有安排行程",
        hint: dayForm.hint || "可以继续补充交通、活动或住宿安排。",
        highlightTag: dayForm.highlightTag || "空闲",
        sortOrder: currentTrip.value.days.length,
      });
    }

    await loadCalendar(currentTrip.value.id, selectedDate.value);
    uni.showToast({ title: "当天摘要已保存", icon: "success" });
  } catch (error) {
    uni.showToast({ title: error instanceof ApiRequestError ? error.message : "保存失败", icon: "none" });
  } finally {
    saving.value = false;
  }
};

const deleteDay = async () => {
  if (!currentTrip.value || !selectedDay.value) return;

  saving.value = true;
  try {
    await tripApi.deleteDay(currentTrip.value.id, selectedDay.value.id);
    const fallbackDate = availableDates.value.find((date) => date !== selectedDate.value) || currentTrip.value.startDate;
    await loadCalendar(currentTrip.value.id, fallbackDate);
    uni.showToast({ title: "当天已删除", icon: "success" });
  } catch (error) {
    uni.showToast({ title: error instanceof ApiRequestError ? error.message : "删除失败", icon: "none" });
  } finally {
    saving.value = false;
  }
};

const saveEvent = async () => {
  if (!currentTrip.value || !selectedDate.value || !eventForm.title) return;

  saving.value = true;
  try {
    const day = await ensureDay();
    await tripApi.createEvent(currentTrip.value.id, {
      tripDayId: day?.id,
      eventType: eventForm.eventType,
      title: eventForm.title,
      description: eventForm.description,
      startAt: `${selectedDate.value}T${eventForm.time}:00.000Z`,
      source: "manual",
      status: "confirmed",
    });

    eventForm.title = "";
    eventForm.description = "";
    eventForm.time = "09:30";
    eventForm.eventType = "activity";

    await loadCalendar(currentTrip.value.id, selectedDate.value);
    uni.showToast({ title: "活动已添加", icon: "success" });
  } catch (error) {
    uni.showToast({ title: error instanceof ApiRequestError ? error.message : "添加活动失败", icon: "none" });
  } finally {
    saving.value = false;
  }
};

const removeEvent = async (eventId: string) => {
  if (!currentTrip.value) return;

  saving.value = true;
  try {
    await tripApi.deleteEvent(eventId);
    await loadCalendar(currentTrip.value.id, selectedDate.value);
  } catch (error) {
    uni.showToast({ title: error instanceof ApiRequestError ? error.message : "删除活动失败", icon: "none" });
  } finally {
    saving.value = false;
  }
};

watch(selectedDay, () => {
  syncDayForm();
});

onLoad(async (query) => {
  const tripId = typeof query?.tripId === "string" ? query.tripId : "";
  await loadTripOptions(tripId);
  if (tripId) {
    selectedTripId.value = tripId;
  }
  await loadCalendar(selectedTripId.value || tripId);
});

onShow(() => {
  if (selectedTripId.value) {
    void loadCalendar(selectedTripId.value, selectedDate.value);
  }
});
</script>

<template>
  <view class="page">
    <view class="header">
      <text class="title">{{ currentTrip ? currentTrip.title : "日历" }}</text>
      <text class="desc">按天维护 TripDay 摘要与 TripEvent 列表。</text>
    </view>

    <view class="panel">
      <text class="panel-title">当前行程</text>
      <picker :range="tripOptions.map((trip) => trip.title)" @change="handleTripChange">
        <view class="picker">{{ currentTrip ? currentTrip.title : "请选择行程" }}</view>
      </picker>
      <text v-if="errorMessage" class="error-text">{{ errorMessage }}</text>
      <text v-else-if="loading" class="helper-text">正在读取服务端日历数据…</text>
    </view>

    <view class="panel">
      <text class="panel-title">行程日期</text>
      <picker mode="date" :value="selectedDate" @change="handleDateChange">
        <view class="picker">{{ selectedDate || "选择日期" }}</view>
      </picker>
      <scroll-view class="date-scroll" scroll-x>
        <view class="date-row">
          <view
            v-for="day in dateChips"
            :key="day.date"
            class="date-chip"
            :class="{ 'date-chip--active': day.date === selectedDate }"
            @tap="selectDate(day.date)"
          >
            <text class="date-chip__date">{{ day.date }}</text>
            <text class="date-chip__label">{{ day.highlightTag }}</text>
          </view>
        </view>
      </scroll-view>
    </view>

    <view class="panel">
      <text class="panel-title">当天摘要</text>
      <input v-model="dayForm.summary" class="input" placeholder="例如：城市探索 / 换城日" />
      <textarea v-model="dayForm.hint" class="textarea" placeholder="补充当天提示信息" />
      <input v-model="dayForm.highlightTag" class="input" placeholder="例如：漫游 / 移动 / 出发" />
      <view class="row-actions">
        <button class="button button--ghost" @tap="deleteDay">删除当天</button>
        <button class="button" :loading="saving" @tap="saveDay">保存摘要</button>
      </view>
    </view>

    <view class="panel">
      <text class="panel-title">新增活动</text>
      <input v-model="eventForm.title" class="input" placeholder="活动标题" />
      <textarea v-model="eventForm.description" class="textarea" placeholder="活动说明" />
      <picker :range="eventTypeOptions" @change="eventForm.eventType = eventTypeOptions[Number($event.detail.value)]">
        <view class="picker">{{ eventForm.eventType }}</view>
      </picker>
      <input v-model="eventForm.time" class="input" placeholder="09:30" />
      <button class="button" :loading="saving" @tap="saveEvent">添加活动</button>
    </view>

    <view class="panel">
      <text class="panel-title">当天活动</text>
      <view v-if="dayEvents.length" class="event-list">
        <view v-for="event in dayEvents" :key="event.id" class="event-card">
          <view>
            <text class="event-title">{{ event.title }}</text>
            <text class="event-meta">{{ event.startAt.slice(11, 16) }} · {{ event.eventType }}</text>
            <text class="event-desc">{{ event.description || "暂无补充说明" }}</text>
          </view>
          <button class="delete-link" @tap="removeEvent(event.id)">删除</button>
        </view>
      </view>
      <text v-else class="empty-text">这一天还没有活动，先从上面新增一条。</text>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 32rpx;
}

.header,
.panel,
.placeholder {
  padding: 28rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.06);
}

.panel,
.placeholder {
  margin-top: 24rpx;
}

.title,
.panel-title,
.placeholder-title {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
  color: #111827;
}

.desc,
.item,
.placeholder-text,
.helper-text,
.error-text {
  display: block;
  margin-top: 12rpx;
  font-size: 28rpx;
  line-height: 1.7;
  color: #6b7280;
}

.error-text {
  color: #be123c;
}

.date-scroll {
  white-space: nowrap;
  margin-top: 18rpx;
}

.date-row {
  display: flex;
  gap: 16rpx;
}

.date-chip {
  min-width: 200rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: #fff4fa;
}

.date-chip--active {
  background: linear-gradient(135deg, #ff6cab, #7f7fd5);
}

.date-chip--active .date-chip__date,
.date-chip--active .date-chip__label {
  color: #ffffff;
}

.date-chip__date,
.date-chip__label {
  display: block;
}

.date-chip__date {
  font-size: 26rpx;
  font-weight: 700;
  color: #111827;
}

.date-chip__label {
  margin-top: 8rpx;
  font-size: 22rpx;
  color: #6b7280;
}

.input,
.textarea,
.picker {
  width: 100%;
  margin-top: 16rpx;
  padding: 22rpx 24rpx;
  border-radius: 22rpx;
  background: #fff4fa;
  font-size: 26rpx;
}

.textarea {
  min-height: 140rpx;
}

.picker {
  color: #6b7280;
}

.row-actions {
  display: flex;
  gap: 16rpx;
  margin-top: 20rpx;
}

.button {
  flex: 1;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #ff6cab, #7f7fd5);
  color: #ffffff;
}

.button--ghost {
  background: #fce7f3;
  color: #be185d;
}

.event-list {
  display: grid;
  gap: 16rpx;
  margin-top: 16rpx;
}

.event-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #fff4fa;
}

.event-title,
.event-meta,
.event-desc,
.empty-text {
  display: block;
}

.event-title {
  font-size: 28rpx;
  font-weight: 700;
  color: #111827;
}

.event-meta,
.event-desc,
.empty-text {
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.delete-link {
  padding: 0;
  background: transparent;
  color: #be185d;
  font-size: 24rpx;
  line-height: 1.5;
}
</style>
