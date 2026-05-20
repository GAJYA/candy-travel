<template>
  <view class="page">
    <view class="topbar">
      <view>
        <text class="brand">AI助手</text>
        <text class="subtitle">小红书行程生成</text>
      </view>
      <view class="topbar-mark">
        <CandyIcon name="ai" />
      </view>
    </view>

    <view v-if="!auth.isAuthenticated" class="candy-card login-card">
      <view class="login-mark">
        <CandyIcon name="ai" />
      </view>
      <text class="login-title">登录后使用 AI 助手</text>
      <text class="login-hint">生成的行程会保存到你的旅行列表</text>
      <button class="candy-btn candy-btn--primary login-btn" :disabled="auth.loading" @click="login">
        {{ auth.loading ? '登录中...' : '微信登录' }}
      </button>
      <text v-if="auth.error" class="candy-text-error login-error">{{ auth.error }}</text>
    </view>

    <view v-else class="ai-workspace">
      <view class="candy-card generator-card">
        <view class="field-block">
          <text class="field-label">小红书分享</text>
          <textarea
            class="share-input"
            v-model="shareText"
            maxlength="4096"
            placeholder="粘贴小红书分享链接或分享文案"
            auto-height
          />
        </view>

        <view class="date-grid">
          <picker mode="date" :value="startDate" @change="onStartDateChange">
            <view class="date-field" :class="{ 'date-field--empty': !startDate }">
              <text class="date-label">开始</text>
              <text class="date-value">{{ startDate || '选择日期' }}</text>
            </view>
          </picker>

          <picker mode="date" :value="endDate || startDate" :start="startDate || undefined" @change="onEndDateChange">
            <view class="date-field" :class="{ 'date-field--empty': !endDate }">
              <text class="date-label">结束</text>
              <text class="date-value">{{ endDate || '选择日期' }}</text>
            </view>
          </picker>
        </view>

        <button
          class="generate-btn"
          :disabled="!canGenerate"
          @click="onGenerateTrip"
        >
          {{ generating ? '生成中...' : '生成行程' }}
        </button>

        <text v-if="errorMessage" class="candy-text-error error-copy">{{ errorMessage }}</text>
      </view>

      <view v-if="lastTrip" class="candy-card result-card" @click="openTrip(lastTrip.id)">
        <view class="result-icon">
          <CandyIcon name="plane" />
        </view>
        <view class="result-copy">
          <text class="result-title">{{ lastTrip.title }}</text>
          <text class="result-meta">{{ formatGeneratedTripMeta(lastTrip) }}</text>
        </view>
        <text class="result-arrow">›</text>
      </view>
    </view>

    <CandyBottomNav active="ai" />
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import CandyBottomNav from '../../components/CandyBottomNav.vue'
import CandyIcon from '../../components/CandyIcon.vue'
import { aiImportApi, type AiTripEventCandidate } from '../../services/ai-import'
import { inspirationApi, type InspirationShareDraft } from '../../services/inspiration'
import { tripApi, type Trip } from '../../services/trip'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const shareText = ref('')
const startDate = ref('')
const endDate = ref('')
const generating = ref(false)
const errorMessage = ref('')
const lastTrip = ref<Trip | null>(null)
const lastEventCount = ref(0)

const shareEventTimes = ['09:00', '11:00', '14:00', '16:00', '19:00']
const shareEventIcons: Record<AiTripEventCandidate['eventType'], string> = {
  transport: 'plane',
  stay: 'hotel',
  activity: 'pin',
  reminder: 'clock',
}

const canGenerate = computed(() => (
  auth.isAuthenticated
  && !generating.value
  && Boolean(shareText.value.trim())
  && Boolean(startDate.value)
  && Boolean(endDate.value)
  && startDate.value <= endDate.value
))

const login = async () => {
  try {
    await auth.login()
  } catch {
    uni.showToast({ title: auth.error || '登录失败', icon: 'none' })
  }
}

const refreshAuth = async () => {
  await auth.bootstrap()
}

const onStartDateChange = (e: any) => {
  startDate.value = String(e.detail.value || '')
  if (endDate.value && endDate.value < startDate.value) {
    endDate.value = startDate.value
  }
}

const onEndDateChange = (e: any) => {
  endDate.value = String(e.detail.value || '')
}

const buildTripTitle = (inspiration: InspirationShareDraft) => {
  const destination = inspiration.destination.trim()
  return destination ? `${destination}旅行` : 'AI生成行程'
}

const buildTripNote = (inspiration: InspirationShareDraft) => {
  return [
    inspiration.note,
    inspiration.planDetail,
    inspiration.sourceUrl ? `来源：${inspiration.sourceUrl}` : null,
  ].filter(Boolean).join('\n\n')
}

const parseDateToUtcMs = (date: string) => {
  const [year, month, day] = date.split('-').map(Number)
  if (!year || !month || !day) return Number.NaN
  return Date.UTC(year, month - 1, day)
}

const formatUtcDate = (ms: number) => {
  const date = new Date(ms)
  return [
    date.getUTCFullYear(),
    String(date.getUTCMonth() + 1).padStart(2, '0'),
    String(date.getUTCDate()).padStart(2, '0'),
  ].join('-')
}

const dateRangeDays = () => {
  const start = parseDateToUtcMs(startDate.value)
  const end = parseDateToUtcMs(endDate.value)
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return 0
  return Math.floor((end - start) / 86400000)
}

const dateFromOffset = (offset: number) => {
  const start = parseDateToUtcMs(startDate.value)
  if (!Number.isFinite(start)) return startDate.value
  return formatUtcDate(start + offset * 86400000)
}

const readDayOffset = (meta: Record<string, unknown>) => {
  const raw = meta.dayOffset
  const value = typeof raw === 'number' ? raw : (typeof raw === 'string' ? Number(raw) : Number.NaN)
  if (!Number.isFinite(value)) return null
  return Math.max(0, Math.floor(value))
}

const buildIsoDateTime = (date: string, time: string) => {
  const parsed = new Date(`${date}T${time}:00`)
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString()
}

const normalizeShareEventCandidates = (events: AiTripEventCandidate[]) => {
  const sortedEvents = [...events].sort((a, b) => (a.sortOrder ?? 0) - (b.sortOrder ?? 0))
  const rangeDays = dateRangeDays()
  const total = Math.max(sortedEvents.length, 1)
  const normalized: AiTripEventCandidate[] = []

  sortedEvents.forEach((candidate, index) => {
    const meta = candidate.meta || {}
    const explicitDayOffset = readDayOffset(meta)
    const fallbackDayOffset = Math.floor((index * (rangeDays + 1)) / total)
    const dayOffset = Math.min(rangeDays, explicitDayOffset ?? fallbackDayOffset)
    const fallbackTime = meta.allDay === true ? '00:00' : shareEventTimes[index % shareEventTimes.length]
    const startAt = candidate.startAt || buildIsoDateTime(dateFromOffset(dayOffset), fallbackTime)
    const title = (candidate.title || candidate.locationName || '').trim()
    if (!title || !startAt) return

    normalized.push({
      ...candidate,
      clientId: candidate.clientId || `xhs_${index + 1}`,
      title,
      startAt,
      endAt: candidate.endAt || null,
      locationName: candidate.locationName || title,
      address: candidate.address || null,
      latitude: candidate.latitude ?? null,
      longitude: candidate.longitude ?? null,
      note: candidate.note || null,
      meta: {
        ...meta,
        icon: typeof meta.icon === 'string' && meta.icon ? meta.icon : shareEventIcons[candidate.eventType],
        allDay: meta.allDay === true,
      },
      warnings: candidate.warnings || [],
      sortOrder: index,
    })
  })

  return normalized
}

const validateInput = () => {
  if (!shareText.value.trim()) return '先粘贴小红书分享链接'
  if (!startDate.value || !endDate.value) return '请选择起止日期'
  if (startDate.value > endDate.value) return '结束日期不能早于开始日期'
  return ''
}

const onGenerateTrip = async () => {
  const validationError = validateInput()
  if (validationError) {
    uni.showToast({ title: validationError, icon: 'none' })
    return
  }

  generating.value = true
  errorMessage.value = ''
  lastEventCount.value = 0
  try {
    const inspiration = await inspirationApi.extractFromShare({
      sharedText: shareText.value.trim(),
      type: 'long',
    })
    const trip = await tripApi.create({
      title: buildTripTitle(inspiration),
      destinationCity: inspiration.destination || undefined,
      status: 'planning',
      startDate: startDate.value,
      endDate: endDate.value,
      note: buildTripNote(inspiration) || undefined,
    })

    const eventCandidates = normalizeShareEventCandidates(inspiration.events || [])
    let eventImportFailed = false
    if (eventCandidates.length) {
      try {
        await aiImportApi.importTripEvents(trip.id, eventCandidates)
        lastEventCount.value = eventCandidates.length
      } catch (e) {
        eventImportFailed = true
        errorMessage.value = e instanceof Error ? e.message : '地点导入失败，请进入行程后手动补充'
      }
    }

    lastTrip.value = trip
    shareText.value = ''
    uni.showToast({
      title: eventImportFailed
        ? '地点导入失败'
        : (lastEventCount.value ? '已生成地点' : '已生成行程'),
      icon: eventImportFailed ? 'none' : 'success',
    })
    uni.navigateTo({ url: `/pages/edit/index?id=${trip.id}` })
  } catch (e) {
    errorMessage.value = e instanceof Error ? e.message : '生成失败，稍后再试'
    uni.showToast({ title: '生成失败', icon: 'none' })
  } finally {
    generating.value = false
  }
}

const openTrip = (id: string) => {
  uni.navigateTo({ url: `/pages/edit/index?id=${id}` })
}

const formatDateRange = (s: string | null, e: string | null) => {
  const sd = s ? s.replace(/-/g, '/') : ''
  const ed = e ? e.replace(/-/g, '/') : ''
  if (sd && ed) return `${sd} → ${ed}`
  if (sd) return `${sd} 出发`
  if (ed) return `${ed} 结束`
  return '日期未定'
}

const formatGeneratedTripMeta = (trip: Trip) => {
  const dateRange = formatDateRange(trip.startDate, trip.endDate)
  return lastEventCount.value ? `${dateRange} · ${lastEventCount.value}个地点` : dateRange
}

onMounted(refreshAuth)
onShow(refreshAuth)
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
    radial-gradient(circle at 10% 0%, rgba(224, 64, 160, 0.14), transparent 34%),
    radial-gradient(circle at 90% 18%, rgba(0, 150, 204, 0.12), transparent 28%),
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

.topbar-mark {
  width: 76rpx;
  height: 76rpx;
  border-radius: $candy-radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-primary;
  background: $candy-primary-fixed;
  box-shadow: $candy-shadow-card;
}

.topbar-mark .candy-icon {
  width: 38rpx;
  height: 38rpx;
  font-size: 38rpx;
}

.login-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $candy-space-sm;
  text-align: center;
}

.login-mark {
  width: 96rpx;
  height: 96rpx;
  border-radius: $candy-radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-primary;
  background: $candy-primary-fixed;
}

.login-mark .candy-icon {
  width: 44rpx;
  height: 44rpx;
  font-size: 44rpx;
}

.login-title {
  font-size: $candy-font-headline-md;
  font-weight: 800;
  color: $candy-on-surface;
  line-height: 1.2;
}

.login-hint,
.login-error {
  font-size: $candy-font-body-md;
}

.login-btn {
  width: 100%;
}

.ai-workspace {
  display: flex;
  flex-direction: column;
  gap: $candy-space-md;
}

.generator-card {
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: $candy-space-xs;
}

.field-label {
  font-size: $candy-font-label-md;
  font-weight: 800;
  color: $candy-on-surface-variant;
}

.share-input {
  box-sizing: border-box;
  width: 100%;
  min-height: 260rpx;
  padding: 28rpx;
  border-radius: $candy-radius;
  border: 2rpx solid $candy-outline-variant;
  background: $candy-surface;
  color: $candy-on-surface;
  font-size: $candy-font-body-md;
  line-height: 1.55;
}

.date-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: $candy-space-sm;
}

.date-field {
  min-width: 0;
  min-height: 132rpx;
  padding: 22rpx 24rpx;
  border-radius: $candy-radius;
  border: 2rpx solid $candy-outline-variant;
  background: $candy-surface-container-lowest;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 8rpx;
}

.date-field--empty .date-value {
  color: $candy-on-surface-variant;
}

.date-label {
  font-size: $candy-font-label-md;
  font-weight: 800;
  color: $candy-on-surface-variant;
}

.date-value {
  font-size: $candy-font-body-lg;
  font-weight: 800;
  color: $candy-on-surface;
  line-height: 1.2;
  word-break: break-all;
}

.generate-btn {
  margin: 8rpx 0 0;
  width: 100%;
  min-height: 96rpx;
  border-radius: $candy-radius-full;
  background: $candy-primary;
  color: $candy-on-primary;
  font-size: $candy-font-body-lg;
  font-weight: 900;
  box-shadow: $candy-shadow-primary;
}

.generate-btn[disabled] {
  background: $candy-outline-variant;
  color: $candy-on-surface-variant;
  box-shadow: none;
}

.error-copy {
  font-size: $candy-font-body-md;
  line-height: 1.45;
}

.result-card {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: $candy-space-sm;
}

.result-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: $candy-radius-full;
  flex: 0 0 72rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-tertiary;
  background: $candy-tertiary-fixed;
}

.result-icon .candy-icon {
  width: 34rpx;
  height: 34rpx;
  font-size: 34rpx;
}

.result-copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.result-title {
  font-size: $candy-font-body-lg;
  font-weight: 900;
  color: $candy-on-surface;
  line-height: 1.25;
}

.result-meta {
  font-size: $candy-font-body-md;
  color: $candy-on-surface-variant;
}

.result-arrow {
  flex: 0 0 auto;
  font-size: 52rpx;
  color: $candy-on-surface-variant;
  line-height: 1;
}
</style>
