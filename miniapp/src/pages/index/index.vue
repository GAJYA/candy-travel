<template>
  <view class="page">
    <view class="topbar">
      <view>
        <text class="brand">P人旅行计划</text>
        <text class="subtitle">{{ subtitle }}</text>
      </view>
      <button
        v-if="auth.isAuthenticated"
        class="topbar-action"
        @click="onShowJoinInvite"
      >
        <text class="topbar-action__mark">#</text>
        <text>加入</text>
      </button>
      <view v-else class="topbar-menu">
        <text>•••</text>
      </view>
    </view>

    <view v-if="!auth.isAuthenticated" class="candy-card login-card">
      <view class="login-mark">
        <text>✦</text>
      </view>
      <text class="login-title">开启你的P人旅行计划</text>
      <text class="login-hint">微信登录后开始整理下一段旅程</text>
      <button class="candy-btn candy-btn--primary login-btn" :disabled="auth.loading" @click="login">
        {{ auth.loading ? '登录中...' : '微信登录' }}
      </button>
      <text v-if="auth.error" class="candy-text-error login-error">{{ auth.error }}</text>
    </view>

    <view v-else class="logged">
      <view v-if="nextTrip" class="countdown-card">
        <view class="countdown-top">
          <text class="countdown-label">下一次旅程开始于</text>
          <text class="countdown-chip">前往 {{ nextTrip.destinationCity || nextTrip.title }}</text>
        </view>
        <view class="countdown-numbers">
          <view class="countdown-unit">
            <text class="countdown-value">{{ countdown.days }}</text>
            <text class="countdown-name">天</text>
          </view>
          <view class="countdown-unit">
            <text class="countdown-value">{{ countdown.hours }}</text>
            <text class="countdown-name">时</text>
          </view>
          <view class="countdown-unit">
            <text class="countdown-value">{{ countdown.minutes }}</text>
            <text class="countdown-name">分</text>
          </view>
        </view>
      </view>

      <view v-else class="countdown-card countdown-card--empty">
        <text class="countdown-label">下一次旅程开始于</text>
        <text class="empty-countdown">先设置出发日期</text>
      </view>

      <button class="new-btn" @click="onCreate">
        <view class="new-btn__icon">
          <text>＋</text>
        </view>
        <view class="new-btn__copy">
          <text class="new-btn__title">新建一次旅行</text>
          <text class="new-btn__hint">规划目的地、时间和出行清单</text>
        </view>
        <text class="new-btn__arrow">›</text>
      </button>

      <view class="section-head">
        <text class="section-icon">✈️</text>
        <text class="section-title">即将出发</text>
      </view>

      <view v-if="trip.listLoading" class="empty">
        <text class="empty-hint">加载中...</text>
      </view>
      <view v-else-if="trip.list.length === 0" class="candy-card empty">
        <text class="empty-emoji">🍬</text>
        <text class="empty-title">还没有任何旅行</text>
        <text class="empty-hint">点上面的按钮，给即将到来的下一段旅程留个位置吧</text>
      </view>
      <view v-else class="trip-list">
        <view
          v-for="t in sortedTrips"
          :key="t.id"
          class="candy-card trip-card"
          @click="onOpen(t.id)"
        >
          <view class="trip-card__rail" />
          <view class="trip-card__content">
            <view class="trip-card__top">
              <text class="candy-tag">{{ statusLabel(t) }}</text>
              <text v-if="t.destinationCity" class="dest">📍 {{ t.destinationCity }}</text>
            </view>
            <text class="trip-card__title">{{ t.title }}</text>
            <text class="trip-card__dates">{{ formatDateRange(t.startDate, t.endDate) }}</text>
          </view>
        </view>
      </view>

      <view class="future-strip">
        <view class="future-strip__item">
          <text class="future-strip__label">计划城市</text>
          <text class="future-strip__value">待统计</text>
        </view>
        <view class="future-strip__item">
          <text class="future-strip__label">预计里程</text>
          <text class="future-strip__value">待统计</text>
        </view>
        <view class="future-strip__item">
          <text class="future-strip__label">我的足迹</text>
          <text class="future-strip__value">待生成</text>
        </view>
      </view>
    </view>

    <view v-if="joinOpen" class="modal-mask" @click="joinOpen = false">
      <view class="join-sheet" @click.stop>
        <view class="join-handle" />
        <view class="join-head">
          <view class="join-mark">
            <text>#</text>
          </view>
          <view class="join-copy">
            <text class="join-title">输入邀请码</text>
            <text class="join-hint">加入好友的同行行程</text>
          </view>
          <button class="join-close" @click="joinOpen = false">×</button>
        </view>
        <view class="code-field">
          <input
            class="code-input"
            :value="inviteCode"
            maxlength="16"
            placeholder="A7K9Q2"
            @input="onInviteCodeInput"
          />
        </view>
        <button
          class="join-submit"
          :disabled="!inviteCode || joiningInvite"
          @click="onJoinInviteSubmit"
        >
          {{ joiningInvite ? '加入中...' : '加入同行' }}
        </button>
      </view>
    </view>

    <CandyBottomNav active="home" />
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import CandyBottomNav from '../../components/CandyBottomNav.vue'
import { tripApi, type Trip } from '../../services/trip'
import { useAuthStore } from '../../stores/auth'
import { useTripStore } from '../../stores/trip'

const auth = useAuthStore()
const trip = useTripStore()
const now = ref(Date.now())
const joinOpen = ref(false)
const inviteCode = ref('')
const joiningInvite = ref(false)
let countdownTimer: ReturnType<typeof setInterval> | null = null

const subtitle = computed(() => {
  if (!auth.isAuthenticated) return '为下一段旅程做准备'
  if (trip.list.length === 0) return '准备开始你的第一次旅行'
  return `共 ${trip.list.length} 段旅程`
})

const sortedTrips = computed(() =>
  [...trip.list].sort((a, b) => dateSortValue(a) - dateSortValue(b)),
)

const nextTrip = computed(() =>
  sortedTrips.value.find((t) => isUpcomingTrip(t)) || null,
)

const countdown = computed(() => {
  const start = nextTrip.value?.startDate
  if (!start) return { days: '--', hours: '--', minutes: '--' }
  const diff = Math.max(0, new Date(`${start}T00:00:00`).getTime() - now.value)
  const totalMinutes = Math.floor(diff / 60000)
  const days = Math.floor(totalMinutes / 1440)
  const hours = Math.floor((totalMinutes % 1440) / 60)
  const minutes = totalMinutes % 60
  return {
    days: String(days).padStart(2, '0'),
    hours: String(hours).padStart(2, '0'),
    minutes: String(minutes).padStart(2, '0'),
  }
})

const statusLabel = (t: Trip): string => {
  if (t.status === 'draft') return t.startDate ? '待完善' : '待排期'
  return ({
    planning: '规划中',
    confirmed: '已确认',
    completed: '已完成',
    canceled: '已取消',
    archived: '已归档',
  }[t.status])
}

const dateSortValue = (t: Trip) => {
  if (!t.startDate) return Number.MAX_SAFE_INTEGER
  return new Date(`${t.startDate}T00:00:00`).getTime()
}

const isUpcomingTrip = (t: Trip) => {
  if (!t.startDate || ['completed', 'canceled', 'archived'].includes(t.status)) return false
  return new Date(`${t.startDate}T23:59:59`).getTime() >= now.value
}

const formatDateRange = (s: string | null, e: string | null) => {
  const sd = s ? s.replace(/-/g, '/') : ''
  const ed = e ? e.replace(/-/g, '/') : ''
  if (sd && ed) return `${sd} → ${ed}`
  if (sd) return `${sd} 出发`
  if (ed) return `${ed} 结束`
  return '日期未定'
}

const login = async () => {
  try {
    await auth.login()
    await trip.loadList()
  } catch {
    uni.showToast({ title: auth.error || '登录失败', icon: 'none' })
  }
}

const onCreate = async () => {
  uni.navigateTo({
    url: '/pages/edit/index?mode=create',
    fail: (err) => {
      uni.showToast({ title: err.errMsg || '打开编辑页失败', icon: 'none' })
    },
  })
}

const onOpen = (id: string) => {
  uni.navigateTo({ url: `/pages/edit/index?id=${id}` })
}

const onShowJoinInvite = () => {
  inviteCode.value = ''
  joinOpen.value = true
}

const normalizeInviteCode = (value: string) =>
  value.replace(/[^a-z0-9]/gi, '').toUpperCase().slice(0, 16)

const onInviteCodeInput = (e: any) => {
  inviteCode.value = normalizeInviteCode(String(e.detail.value || ''))
}

const onJoinInviteSubmit = async () => {
  const code = normalizeInviteCode(inviteCode.value)
  if (!code || joiningInvite.value) return
  joiningInvite.value = true
  try {
    const accepted = await tripApi.acceptInvite(code)
    await trip.loadList()
    joinOpen.value = false
    uni.showToast({ title: '已加入同行', icon: 'success' })
    uni.navigateTo({ url: `/pages/edit/index?id=${accepted.tripId}` })
  } catch (e) {
    uni.showToast({ title: e instanceof Error ? e.message : '加入失败', icon: 'none' })
  } finally {
    joiningInvite.value = false
  }
}

const refreshIfAuthed = async () => {
  await auth.bootstrap()
  if (auth.isAuthenticated) await trip.loadList()
}

onMounted(() => {
  void refreshIfAuthed()
  countdownTimer = setInterval(() => {
    now.value = Date.now()
  }, 60000)
})
onShow(refreshIfAuthed)
onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<style lang="scss">
.page {
  min-height: 100vh;
  padding: 36rpx $candy-gutter 220rpx;
  padding-bottom: calc(220rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: $candy-space-md;
  background:
    radial-gradient(circle at 14% 2%, rgba(224, 64, 160, 0.14), transparent 34%),
    radial-gradient(circle at 88% 18%, rgba(0, 150, 204, 0.12), transparent 26%),
    $candy-background;
}

.topbar {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: $candy-space-xs 0 0;
}
.brand {
  display: block;
  font-size: 54rpx;
  font-weight: 800;
  color: $candy-on-background;
  line-height: 1.1;
}
.subtitle {
  display: block;
  margin-top: 6rpx;
  font-size: $candy-font-body-md;
  color: $candy-on-surface-variant;
}
.topbar-menu {
  width: 64rpx;
  height: 64rpx;
  border-radius: $candy-radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-on-surface;
  background: $candy-surface-container-lowest;
  box-shadow: $candy-shadow-card;
}
.topbar-action {
  margin: 0;
  min-width: 112rpx;
  height: 64rpx;
  line-height: 64rpx;
  padding: 0 22rpx;
  border-radius: $candy-radius-full;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  background: $candy-surface-container-lowest;
  color: $candy-primary;
  font-size: $candy-font-label-md;
  font-weight: 900;
  box-shadow: $candy-shadow-card;
}
.topbar-action::after {
  border: none;
}
.topbar-action__mark {
  color: $candy-secondary;
  font-size: 26rpx;
  font-weight: 900;
}

.logged {
  display: flex;
  flex-direction: column;
  gap: $candy-space-md;
}

.countdown-card {
  padding: 32rpx;
  border-radius: $candy-radius-lg;
  background: $candy-primary;
  color: $candy-on-primary;
  box-shadow: $candy-shadow-primary;
}
.countdown-card--empty {
  display: flex;
  flex-direction: column;
  gap: $candy-space-xs;
}
.countdown-top {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: $candy-space-sm;
}
.countdown-label {
  font-size: $candy-font-label-md;
  font-weight: 700;
  opacity: 0.88;
}
.countdown-chip {
  max-width: 330rpx;
  padding: 8rpx 18rpx;
  border-radius: $candy-radius-full;
  background: rgba(255, 255, 255, 0.22);
  font-size: $candy-font-label-md;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.countdown-numbers {
  display: flex;
  flex-direction: row;
  gap: $candy-space-sm;
  margin-top: $candy-space-md;
}
.countdown-unit {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.countdown-value {
  font-size: 58rpx;
  font-weight: 900;
  line-height: 1;
}
.countdown-name {
  margin-top: 8rpx;
  font-size: $candy-font-label-md;
  opacity: 0.86;
}
.empty-countdown {
  font-size: $candy-font-headline-md;
  font-weight: 800;
}

.new-btn {
  width: 100%;
  min-height: 112rpx;
  margin: 0;
  padding: 22rpx 24rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: $candy-space-sm;
  border: 2rpx solid rgba(224, 64, 160, 0.18);
  border-radius: $candy-radius-md;
  background: linear-gradient(135deg, #ffffff 0%, $candy-surface-container-low 100%);
  box-shadow: 0 10rpx 28rpx rgba(96, 72, 104, 0.09);
  text-align: left;
  line-height: 1.35;
}
.new-btn::after {
  border: none;
}
.new-btn__icon {
  flex: 0 0 56rpx;
  width: 56rpx;
  height: 56rpx;
  border-radius: $candy-radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $candy-primary;
  color: $candy-on-primary;
  box-shadow: 0 8rpx 20rpx rgba(224, 64, 160, 0.22);
  font-size: 34rpx;
  font-weight: 800;
}
.new-btn__copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.new-btn__title {
  color: $candy-on-surface;
  font-size: 30rpx;
  font-weight: 800;
}
.new-btn__hint {
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  font-weight: 500;
}
.new-btn__arrow {
  flex: 0 0 auto;
  color: $candy-primary;
  font-size: 42rpx;
  font-weight: 800;
  line-height: 1;
}
.section-head {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: $candy-space-xs;
}
.section-icon {
  font-size: 30rpx;
}
.section-title {
  font-size: $candy-font-body-lg;
  font-weight: 800;
  color: $candy-on-surface;
}

.trip-list {
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
}
.trip-card {
  position: relative;
  min-height: 150rpx;
  padding: 0;
  overflow: hidden;
}
.trip-card__rail {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 12rpx;
  background: $candy-primary;
}
.trip-card__content {
  padding: 28rpx 32rpx 28rpx 40rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}
.trip-card__top {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: $candy-space-sm;
}
.dest {
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
}
.trip-card__title {
  font-size: 40rpx;
  font-weight: 900;
  color: $candy-on-surface;
  line-height: 1.18;
}
.trip-card__dates {
  color: $candy-on-surface-variant;
  font-size: $candy-font-body-md;
}

.future-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12rpx;
  padding: 14rpx;
  border: 2rpx dashed rgba(157, 132, 152, 0.26);
  border-radius: $candy-radius-md;
  background: rgba(255, 255, 255, 0.48);
}
.future-strip__item {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  padding: 10rpx 8rpx;
  text-align: center;
}
.future-strip__label {
  color: rgba(96, 72, 104, 0.62);
  font-size: 22rpx;
  font-weight: 700;
}
.future-strip__value {
  color: rgba(96, 72, 104, 0.46);
  font-size: 20rpx;
  font-weight: 700;
}

.login-card,
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $candy-space-sm;
  padding: $candy-space-md;
}
.login-mark {
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  background: $candy-primary-fixed;
  color: $candy-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  font-weight: 900;
}
.login-title,
.empty-title {
  font-size: $candy-font-headline-md;
  font-weight: 800;
  color: $candy-on-surface;
  text-align: center;
}
.login-hint,
.empty-hint {
  font-size: $candy-font-body-md;
  color: $candy-on-surface-variant;
  text-align: center;
}
.login-btn {
  width: 100%;
}
.login-error {
  font-size: $candy-font-label-md;
  text-align: center;
}
.empty-emoji {
  font-size: 80rpx;
}
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  display: flex;
  align-items: flex-end;
  background: rgba(40, 19, 48, 0.4);
}
.join-sheet {
  width: 100%;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
  padding: 18rpx $candy-space-md 30rpx;
  border-top-left-radius: $candy-radius-md;
  border-top-right-radius: $candy-radius-md;
  background: $candy-surface-container-lowest;
}
.join-handle {
  align-self: center;
  width: 72rpx;
  height: 8rpx;
  border-radius: $candy-radius-full;
  background: $candy-outline-variant;
}
.join-head {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 18rpx;
}
.join-mark {
  flex: 0 0 64rpx;
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $candy-primary-fixed;
  color: $candy-primary;
  font-size: 34rpx;
  font-weight: 900;
}
.join-copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}
.join-title {
  color: $candy-on-surface;
  font-size: 38rpx;
  font-weight: 800;
}
.join-hint {
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
}
.join-close {
  margin: 0;
  flex: 0 0 58rpx;
  width: 58rpx;
  height: 58rpx;
  line-height: 58rpx;
  padding: 0;
  border-radius: 50%;
  background: $candy-surface-container;
  color: $candy-on-surface-variant;
  font-size: 34rpx;
  font-weight: 700;
}
.join-close::after {
  border: none;
}
.code-field {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 108rpx;
  padding: 0 24rpx;
  border-radius: $candy-radius-sm;
  background: $candy-surface-container-low;
  border: 2rpx solid $candy-outline-variant;
}
.code-input {
  width: 100%;
  min-height: 72rpx;
  text-align: center;
  letter-spacing: 10rpx;
  color: $candy-primary;
  font-size: 48rpx;
  font-weight: 900;
}
.join-submit {
  margin: 0;
  width: 100%;
  height: 88rpx;
  line-height: 88rpx;
  padding: 0;
  border-radius: $candy-radius-full;
  background: $candy-primary;
  color: $candy-on-primary;
  font-size: $candy-font-body-lg;
  font-weight: 900;
  box-shadow: 0 12rpx 30rpx rgba(224, 64, 160, 0.2);
}
.join-submit::after {
  border: none;
}
.join-submit[disabled] {
  background: $candy-outline-variant;
  color: $candy-on-surface-variant;
  box-shadow: none;
}
</style>
