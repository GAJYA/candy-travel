<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";
import { ApiRequestError, homeApi, type HomeOverviewResponse } from "../../services/api";

type HomeTripCard = HomeOverviewResponse["upcomingTrips"][number] & {
  dateLabel: string;
  distanceKm: number;
};

const loading = ref(false);
const errorMessage = ref("");
const upcomingTrips = ref<HomeOverviewResponse["upcomingTrips"]>([]);
const overviewStats = ref<HomeOverviewResponse["stats"]>({
  plannedCities: 0,
  tripCount: 0,
  confirmedTripCount: 0,
});

const tripStatusLabel: Record<string, string> = {
  draft: "草稿",
  planning: "规划中",
  confirmed: "已确认",
  completed: "已完成",
  archived: "已归档",
};

const transportDistance: Record<string, number> = {
  flight: 1760,
  train: 460,
  bus: 180,
  car: 260,
};

const formatDateRange = (startDate: string, endDate: string) => {
  const formatter = new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "numeric",
    day: "numeric",
  });

  return `${formatter.format(new Date(`${startDate}T00:00:00`))} - ${formatter.format(new Date(`${endDate}T00:00:00`))}`;
};

const countdown = computed(() => {
  const nextTrip = [...upcomingTrips.value]
    .filter((trip) => new Date(`${trip.startDate}T09:00:00`).getTime() > Date.now())
    .sort((left, right) => left.startDate.localeCompare(right.startDate))[0];

  if (!nextTrip) return null;

  const diffMs = new Date(`${nextTrip.startDate}T09:00:00`).getTime() - Date.now();
  const totalMinutes = Math.max(Math.floor(diffMs / 60000), 0);
  const days = Math.floor(totalMinutes / (60 * 24));
  const hours = Math.floor((totalMinutes % (60 * 24)) / 60);
  const minutes = totalMinutes % 60;

  return {
    days: `${days}`.padStart(2, "0"),
    hours: `${hours}`.padStart(2, "0"),
    minutes: `${minutes}`.padStart(2, "0"),
    destinationCity: nextTrip.destinationCity,
  };
});

const stats = computed(() => ({
  plannedCities: overviewStats.value.plannedCities,
  tripCount: overviewStats.value.tripCount,
  distanceKm: upcomingTrips.value.reduce(
    (sum, trip) => sum + (transportDistance[trip.primaryTransportMode] ?? transportDistance.flight),
    0,
  ),
}));

const tripCards = computed<HomeTripCard[]>(() =>
  upcomingTrips.value.slice(0, 3).map((trip) => ({
    ...trip,
    dateLabel: formatDateRange(trip.startDate, trip.endDate),
    distanceKm: transportDistance[trip.primaryTransportMode] ?? transportDistance.flight,
  })),
);

const loadOverview = async () => {
  loading.value = true;
  errorMessage.value = "";

  try {
    const response = await homeApi.getOverview();
    upcomingTrips.value = response.upcomingTrips;
    overviewStats.value = response.stats;
  } catch (error) {
    errorMessage.value = error instanceof ApiRequestError ? error.message : "首页数据加载失败";
  } finally {
    loading.value = false;
  }
};

const openTripPage = (tripId: string, page: "calendar" | "edit") => {
  uni.navigateTo({
    url: `/pages/${page}/index?tripId=${tripId}`,
  });
};

onShow(() => {
  void loadOverview();
});
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="eyebrow">CandyTravel / Mini Program</text>
      <text class="title">下一次冒险开始于</text>
      <view class="countdown">
        <view class="countdown-item">
          <text class="countdown-value">{{ countdown?.days ?? "00" }}</text>
          <text class="countdown-label">天</text>
        </view>
        <text class="countdown-sep">:</text>
        <view class="countdown-item">
          <text class="countdown-value">{{ countdown?.hours ?? "00" }}</text>
          <text class="countdown-label">时</text>
        </view>
        <text class="countdown-sep">:</text>
        <view class="countdown-item">
          <text class="countdown-value">{{ countdown?.minutes ?? "00" }}</text>
          <text class="countdown-label">分</text>
        </view>
      </view>
      <text class="subtitle">前往 {{ countdown?.destinationCity ?? "下一站" }}</text>
    </view>

    <view class="section">
      <text class="section-title">年度旅行概览</text>
      <view class="stats-grid">
        <view class="stat-card">
          <text class="stat-value">{{ stats.plannedCities }}</text>
          <text class="stat-label">计划城市</text>
        </view>
        <view class="stat-card">
          <text class="stat-value">{{ stats.tripCount }}</text>
          <text class="stat-label">旅行次数</text>
        </view>
        <view class="stat-card stat-card--wide">
          <text class="stat-value">{{ stats.distanceKm.toLocaleString("zh-CN") }}</text>
          <text class="stat-label">累计里程 km</text>
        </view>
      </view>
    </view>

    <view class="section">
      <view class="section-header">
        <text class="section-title">即将到来的行程</text>
        <navigator class="assistant-link" url="/pages/ai/index">AI 文本提取</navigator>
      </view>
      <text v-if="loading" class="note-text">正在读取服务端行程概览…</text>
      <text v-else-if="errorMessage" class="note-text note-text--error">{{ errorMessage }}</text>
      <view class="trip-list">
        <view v-for="trip in tripCards" :key="trip.id" class="trip-card">
          <view class="trip-main" @tap="openTripPage(trip.id, 'calendar')">
            <view>
              <text class="trip-title">{{ trip.title }}</text>
              <text class="trip-subtitle">{{ trip.dateLabel }}</text>
              <text class="trip-subtitle">{{ trip.destinationCity }}</text>
            </view>
            <view class="trip-meta">
              <text class="trip-status">{{ tripStatusLabel[trip.status] }}</text>
              <text class="trip-distance">{{ trip.distanceKm }} km</text>
            </view>
          </view>
          <button class="secondary-button" @tap="openTripPage(trip.id, 'edit')">编辑计划</button>
        </view>
        <text v-if="!loading && !errorMessage && !tripCards.length" class="note-text">后端当前还没有旅行计划，先去 AI 页或编辑页创建。</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 32rpx;
}

.hero {
  padding: 36rpx;
  border-radius: 36rpx;
  background: linear-gradient(135deg, #ff6cab, #7f7fd5);
  color: #fff;
  box-shadow: 0 18rpx 40rpx rgba(255, 108, 171, 0.2);
}

.eyebrow {
  display: block;
  font-size: 22rpx;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  opacity: 0.86;
}

.title {
  display: block;
  margin-top: 12rpx;
  font-size: 44rpx;
  font-weight: 700;
}

.subtitle {
  display: block;
  margin-top: 20rpx;
  font-size: 28rpx;
  line-height: 1.5;
  opacity: 0.92;
}

.countdown {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24rpx;
}

.countdown-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.countdown-value {
  font-size: 56rpx;
  font-weight: 800;
}

.countdown-label,
.countdown-sep {
  font-size: 24rpx;
  opacity: 0.85;
}

.countdown-sep {
  margin: 0 16rpx;
}

.section {
  margin-top: 32rpx;
}

.section-title {
  display: block;
  margin-bottom: 20rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: #374151;
}

.grid {
  display: grid;
  gap: 20rpx;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
}

.stat-card {
  padding: 28rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.06);
}

.stat-card--wide {
  grid-column: span 2;
}

.stat-value {
  display: block;
  font-size: 44rpx;
  font-weight: 800;
  color: #111827;
}

.stat-label {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.assistant-link {
  font-size: 24rpx;
  color: #7f56d9;
}

.note-text {
  display: block;
  margin-bottom: 16rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.note-text--error {
  color: #be123c;
}

.trip-list {
  display: grid;
  gap: 20rpx;
}

.trip-card {
  padding: 28rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.06);
}

.trip-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.trip-title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: #111827;
}

.trip-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  color: #6b7280;
}

.trip-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.trip-status {
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #fce7f3;
  font-size: 22rpx;
  color: #be185d;
}

.trip-distance {
  margin-top: 14rpx;
  font-size: 22rpx;
  color: #6b7280;
}

.secondary-button {
  margin-top: 20rpx;
  border-radius: 999rpx;
  background: #fff4fa;
  color: #d946ef;
}

.card,
.note {
  display: block;
  padding: 28rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 30rpx rgba(15, 23, 42, 0.06);
}

.card-title {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: #111827;
}

.card-desc,
.note text {
  display: block;
  margin-top: 10rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: #6b7280;
}
</style>
