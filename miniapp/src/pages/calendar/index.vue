<template>
  <view class="page">
    <view class="topbar">
      <view>
        <text class="brand">旅行日历</text>
        <text class="subtitle">{{ subtitle }}</text>
      </view>
      <button class="today-btn" @click="goToday">今天</button>
    </view>

    <view v-if="!auth.isAuthenticated" class="login-panel">
      <view class="login-mark">
        <CandyIcon name="calendar" />
      </view>
      <text class="login-title">登录后查看旅行日历</text>
      <text class="login-hint">把行程和事件按日期串起来</text>
      <button class="candy-btn candy-btn--primary login-btn" :disabled="auth.loading" @click="login">
        {{ auth.loading ? '登录中...' : '微信登录' }}
      </button>
      <text v-if="auth.error" class="candy-text-error login-error">{{ auth.error }}</text>
    </view>

    <view v-else class="calendar-content">
      <view class="calendar-card">
        <view class="month-head">
          <button class="month-btn" @click="shiftMonth(-1)">‹</button>
          <text class="month-title">{{ currentMonthLabel }}</text>
          <button class="month-btn" @click="shiftMonth(1)">›</button>
        </view>

        <view class="weekday-row">
          <text v-for="day in weekdays" :key="day" class="weekday">{{ day }}</text>
        </view>

        <view class="calendar-grid">
          <view
            v-for="cell in calendarCells"
            :key="cell.date"
            class="calendar-day"
            :class="{
              'calendar-day--muted': !cell.inMonth,
              'calendar-day--today': cell.isToday,
              'calendar-day--selected': cell.date === selectedDate,
              'calendar-day--filled': cell.tripCount > 0 || cell.eventCount > 0,
            }"
            @click="selectDate(cell.date)"
          >
            <text class="calendar-day__num">{{ cell.day }}</text>
            <view class="calendar-day__marks">
              <text v-if="cell.tripCount" class="calendar-day__trip-mark">旅</text>
              <text v-if="cell.eventCount" class="calendar-day__event-mark">{{ cell.eventCount }}</text>
            </view>
          </view>
        </view>
      </view>

      <view class="day-panel">
        <view class="day-panel__head">
          <view>
            <text class="day-panel__date">{{ timelineTitle }}</text>
            <text class="day-panel__hint">{{ timelineHint }}</text>
          </view>
          <button
            v-if="selectedPrimaryTripId"
            class="day-panel__action"
            @click="openTrip(selectedPrimaryTripId)"
          >
            编辑行程
          </button>
          <button
            v-else-if="canCreateTripForSelectedDate"
            class="day-panel__action"
            @click="createTripForSelectedDate"
          >
            新建行程
          </button>
        </view>

        <view v-if="canShowTripOverview" class="timeline-switch">
          <view
            class="timeline-switch__item"
            :class="{ 'timeline-switch__item--active': visibleTimelineMode === 'day' }"
            @click="setTimelineMode('day')"
          >
            <text>当天安排</text>
          </view>
          <view
            class="timeline-switch__item"
            :class="{ 'timeline-switch__item--active': visibleTimelineMode === 'trip' }"
            @click="setTimelineMode('trip')"
          >
            <text>行程总览</text>
          </view>
        </view>

        <scroll-view
          v-if="visibleTimelineMode === 'trip' && selectedTrips.length > 1"
          scroll-x
          class="trip-chip-row"
        >
          <view class="trip-chip-track">
            <view
              v-for="item in selectedTrips"
              :key="item.id"
              class="trip-chip"
              :class="{ 'trip-chip--active': item.id === selectedOverviewTripId }"
              @click="selectOverviewTrip(item.id)"
            >
              <text>{{ item.title }}</text>
            </view>
          </view>
        </scroll-view>

        <view v-if="loading" class="empty-day">
          <text>加载中...</text>
        </view>
        <view v-else-if="visibleTimelineMode === 'day' && selectedItems.length === 0" class="empty-day">
          <text class="empty-day__title">这天还没有安排</text>
          <text class="empty-day__hint">可以从这一天开始创建一段旅行</text>
        </view>
        <view v-else-if="visibleTimelineMode === 'day'" class="schedule-list">
          <view
            v-for="item in selectedItems"
            :key="item.id"
            class="schedule-item"
            :class="`schedule-item--${item.tone}`"
            @click="openTrip(item.tripId)"
          >
            <view class="schedule-item__time">
              <text>{{ item.timeLabel }}</text>
            </view>
            <view class="schedule-item__rail">
              <view class="schedule-item__dot">
                <CandyIcon :name="item.icon" />
              </view>
            </view>
            <view class="schedule-item__body">
              <text class="schedule-item__trip">{{ item.tripTitle }}</text>
              <text class="schedule-item__title">{{ item.title }}</text>
              <text v-if="item.locationName" class="schedule-item__meta">{{ item.locationName }}</text>
            </view>
          </view>
        </view>
        <view v-else-if="overviewGroups.length === 0" class="empty-day">
          <text class="empty-day__title">这段行程还没有安排</text>
          <text class="empty-day__hint">添加事件后会按日期整理在这里</text>
        </view>
        <view v-else class="overview-list">
          <view v-for="group in overviewGroups" :key="group.date" class="overview-group">
            <view class="overview-group__head">
              <text class="overview-group__date">{{ group.label }}</text>
              <text class="overview-group__count">{{ group.items.length }} 项</text>
            </view>
            <view class="schedule-list">
              <view
                v-for="item in group.items"
                :key="item.id"
                class="schedule-item"
                :class="`schedule-item--${item.tone}`"
                @click="openTrip(item.tripId)"
              >
                <view class="schedule-item__time">
                  <text>{{ item.timeLabel }}</text>
                </view>
                <view class="schedule-item__rail">
                  <view class="schedule-item__dot">
                    <CandyIcon :name="item.icon" />
                  </view>
                </view>
                <view class="schedule-item__body">
                  <text class="schedule-item__trip">{{ item.tripTitle }}</text>
                  <text class="schedule-item__title">{{ item.title }}</text>
                  <text v-if="item.locationName" class="schedule-item__meta">{{ item.locationName }}</text>
                </view>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <CandyBottomNav active="calendar" />
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import CandyBottomNav from '../../components/CandyBottomNav.vue'
import CandyIcon from '../../components/CandyIcon.vue'
import type { Trip } from '../../services/trip'
import { tripEventApi, type TripEvent } from '../../services/trip-event'
import { useAuthStore } from '../../stores/auth'
import { useTripStore } from '../../stores/trip'
import { sortTripsForDisplay } from '../../utils/trip-sort'

interface CalendarCell {
  date: string
  day: number
  inMonth: boolean
  isToday: boolean
  tripCount: number
  eventCount: number
}

interface ScheduleItem {
  id: string
  tripId: string
  tripTitle: string
  title: string
  timeLabel: string
  locationName: string
  icon: string
  tone: 'trip' | 'event'
  sort: number
}

interface OverviewGroup {
  date: string
  label: string
  items: ScheduleItem[]
}

type TimelineMode = 'day' | 'trip'

const auth = useAuthStore()
const trip = useTripStore()
const today = todayKey()
const currentMonth = ref(monthStart(parseDate(today)))
const selectedDate = ref(today)
const timelineMode = ref<TimelineMode>('day')
const overviewTripId = ref('')
const loading = ref(false)
const eventsByTrip = ref<Record<string, TripEvent[]>>({})
const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const iconValues = new Set([
  'hotel',
  'plane',
  'train',
  'bus',
  'car',
  'ship',
  'food',
  'coffee',
  'museum',
  'park',
  'shopping',
  'ticket',
  'camera',
  'spa',
  'luggage',
  'clock',
  'pin',
  'sparkle',
])

const legacyIconMap: Record<string, string> = {
  '🏨': 'hotel',
  '✈️': 'plane',
  '🚄': 'train',
  '🚌': 'bus',
  '🚗': 'car',
  '🚕': 'car',
  '🚢': 'ship',
  '🍽️': 'food',
  '☕': 'coffee',
  '🏛️': 'museum',
  '🌿': 'park',
  '🎫': 'ticket',
  '📸': 'camera',
  '⏰': 'clock',
  '📌': 'pin',
}

const sortedTrips = computed(() => sortTripsForDisplay(trip.list))

const subtitle = computed(() => {
  if (!auth.isAuthenticated) return '按日期查看下一段安排'
  if (trip.listLoading || loading.value) return '正在整理你的行程'
  if (sortedTrips.value.length === 0) return '暂无旅行计划'
  return `共 ${sortedTrips.value.length} 段旅程`
})

const currentMonthLabel = computed(() => (
  `${currentMonth.value.getFullYear()}年${currentMonth.value.getMonth() + 1}月`
))

const tripDayCounts = computed(() => {
  const counts = new Map<string, number>()
  sortedTrips.value.forEach((item) => {
    if (!item.startDate) return
    const endDate = item.endDate || item.startDate
    eachDate(item.startDate, endDate).forEach((date) => {
      counts.set(date, (counts.get(date) || 0) + 1)
    })
  })
  return counts
})

const eventDayCounts = computed(() => {
  const counts = new Map<string, number>()
  Object.values(eventsByTrip.value).flat().forEach((event) => {
    const date = datePart(event.startAt)
    counts.set(date, (counts.get(date) || 0) + 1)
  })
  return counts
})

const calendarCells = computed<CalendarCell[]>(() => {
  const first = monthStart(currentMonth.value)
  const gridStart = addDays(first, -first.getDay())
  return Array.from({ length: 42 }, (_, index) => {
    const date = addDays(gridStart, index)
    const key = formatDate(date)
    return {
      date: key,
      day: date.getDate(),
      inMonth: date.getMonth() === first.getMonth(),
      isToday: key === today,
      tripCount: tripDayCounts.value.get(key) || 0,
      eventCount: eventDayCounts.value.get(key) || 0,
    }
  })
})

const selectedTrips = computed(() =>
  sortedTrips.value.filter((item) => isDateInsideTrip(selectedDate.value, item)),
)

const selectedItems = computed<ScheduleItem[]>(() => {
  const items: ScheduleItem[] = []
  selectedTrips.value.forEach((item) => {
    if (item.startDate === selectedDate.value) {
      items.push(createTripStartItem(item))
    } else if (item.endDate === selectedDate.value) {
      items.push(createTripEndItem(item))
    } else {
      items.push(createTripMidItem(item))
    }
  })

  Object.entries(eventsByTrip.value).forEach(([tripId, events]) => {
    const parentTrip = sortedTrips.value.find((item) => item.id === tripId)
    events.forEach((event) => {
      if (datePart(event.startAt) !== selectedDate.value) return
      items.push(createEventItem(event, parentTrip))
    })
  })

  return items.sort((a, b) => a.sort - b.sort)
})

const selectedDateLabel = computed(() => {
  const d = parseDate(selectedDate.value)
  return `${d.getMonth() + 1}月${d.getDate()}日 星期${weekdays[d.getDay()]}`
})

const selectedPrimaryTripId = computed(() => selectedTrips.value[0]?.id || selectedItems.value[0]?.tripId || '')

const canShowTripOverview = computed(() => selectedTrips.value.length > 0)

const visibleTimelineMode = computed<TimelineMode>(() => (
  canShowTripOverview.value ? timelineMode.value : 'day'
))

const canCreateTripForSelectedDate = computed(() => (
  visibleTimelineMode.value === 'day' && selectedItems.value.length === 0
))

const selectedOverviewTripId = computed(() => {
  if (selectedTrips.value.some((item) => item.id === overviewTripId.value)) return overviewTripId.value
  return selectedTrips.value[0]?.id || ''
})

const selectedOverviewTrip = computed(() =>
  selectedTrips.value.find((item) => item.id === selectedOverviewTripId.value) || null,
)

const overviewGroups = computed<OverviewGroup[]>(() => {
  const activeTrip = selectedOverviewTrip.value
  if (!activeTrip?.startDate) return []
  const endDate = activeTrip.endDate || activeTrip.startDate
  const tripEvents = eventsByTrip.value[activeTrip.id] || []

  return eachDate(activeTrip.startDate, endDate).reduce<OverviewGroup[]>((groups, date) => {
    const items: ScheduleItem[] = []
    if (date === activeTrip.startDate) items.push(createTripStartItem(activeTrip))
    tripEvents.forEach((event) => {
      if (datePart(event.startAt) === date) items.push(createEventItem(event, activeTrip))
    })
    if (date === endDate && endDate !== activeTrip.startDate) items.push(createTripEndItem(activeTrip))
    if (items.length > 0) {
      groups.push({
        date,
        label: compactDateLabel(date),
        items: items.sort((a, b) => a.sort - b.sort),
      })
    }
    return groups
  }, [])
})

const timelineTitle = computed(() => (
  visibleTimelineMode.value === 'trip'
    ? selectedOverviewTrip.value?.title || '行程总览'
    : selectedDateLabel.value
))

const timelineHint = computed(() => {
  if (visibleTimelineMode.value === 'trip') {
    const count = overviewGroups.value.reduce((sum, group) => sum + group.items.length, 0)
    return count ? `${compactRangeLabel(selectedOverviewTrip.value)} · ${count} 项安排` : '暂无安排'
  }
  return selectedItems.value.length ? `${selectedItems.value.length} 项安排` : '暂无安排'
})

const setTimelineMode = (mode: TimelineMode) => {
  timelineMode.value = mode
}

const selectOverviewTrip = (tripId: string) => {
  overviewTripId.value = tripId
}

const login = async () => {
  try {
    await auth.login()
    await loadCalendar()
  } catch {
    uni.showToast({ title: auth.error || '登录失败', icon: 'none' })
  }
}

const loadCalendar = async () => {
  await auth.bootstrap()
  if (!auth.isAuthenticated) return
  loading.value = true
  try {
    await trip.loadList()
    const loaded: Record<string, TripEvent[]> = {}
    await Promise.all(sortedTrips.value.map(async (item) => {
      try {
        loaded[item.id] = await tripEventApi.list(item.id)
      } catch {
        loaded[item.id] = []
      }
    }))
    eventsByTrip.value = loaded
    focusUsefulDate()
  } finally {
    loading.value = false
  }
}

const focusUsefulDate = () => {
  if (selectedItems.value.length > 0) return
  const next = sortedTrips.value.find((item) => item.startDate && isUpcomingTrip(item))
  const fallback = next?.startDate || sortedTrips.value.find((item) => item.startDate)?.startDate
  if (!fallback) return
  selectedDate.value = fallback
  currentMonth.value = monthStart(parseDate(fallback))
}

const selectDate = (date: string) => {
  selectedDate.value = date
  if (!selectedTrips.value.some((item) => item.id === overviewTripId.value)) {
    overviewTripId.value = selectedTrips.value[0]?.id || ''
  }
  const selected = parseDate(date)
  if (!isSameMonth(selected, currentMonth.value)) {
    currentMonth.value = monthStart(selected)
  }
}

const shiftMonth = (offset: number) => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + offset, 1)
}

const goToday = () => {
  selectedDate.value = today
  currentMonth.value = monthStart(parseDate(today))
}

const openTrip = (tripId: string) => {
  if (!tripId) return
  uni.navigateTo({ url: `/pages/edit/index?id=${tripId}` })
}

const createTripForSelectedDate = () => {
  const date = encodeURIComponent(selectedDate.value)
  uni.navigateTo({
    url: `/pages/edit/index?mode=create&startDate=${date}&endDate=${date}`,
    fail: (err) => {
      uni.showToast({ title: err.errMsg || '打开编辑页失败', icon: 'none' })
    },
  })
}

const eventIconName = (event: TripEvent) => {
  if (typeof event.meta?.icon === 'string' && event.meta.icon) {
    return normalizeIcon(event.meta.icon)
  }
  return ({ transport: 'plane', stay: 'hotel', reminder: 'clock', activity: 'pin' }[event.eventType] || 'pin')
}

const normalizeIcon = (icon: string) => {
  if (iconValues.has(icon)) return icon
  return legacyIconMap[icon] || 'pin'
}

const eventTimeRange = (event: TripEvent) => {
  if (event.meta?.allDay === true) return '全天'
  const start = formatEventTime(event.startAt)
  if (!event.endAt) return start
  return `${start}-${formatEventTime(event.endAt)}`
}

function createTripStartItem(item: Trip): ScheduleItem {
  return {
    id: `trip-start-${item.id}`,
    tripId: item.id,
    tripTitle: item.title,
    title: `${item.destinationCity || item.title} 出发`,
    timeLabel: '出发',
    locationName: formatDateRange(item.startDate, item.endDate),
    icon: 'plane',
    tone: 'trip',
    sort: 0,
  }
}

function createTripEndItem(item: Trip): ScheduleItem {
  return {
    id: `trip-end-${item.id}`,
    tripId: item.id,
    tripTitle: item.title,
    title: '行程结束',
    timeLabel: '结束',
    locationName: item.destinationCity || '',
    icon: 'check',
    tone: 'trip',
    sort: 9998,
  }
}

function createTripMidItem(item: Trip): ScheduleItem {
  return {
    id: `trip-mid-${item.id}`,
    tripId: item.id,
    tripTitle: item.title,
    title: '行程进行中',
    timeLabel: '旅程',
    locationName: item.destinationCity || '',
    icon: 'pin',
    tone: 'trip',
    sort: 9997,
  }
}

function createEventItem(event: TripEvent, parentTrip?: Trip | null): ScheduleItem {
  return {
    id: event.id,
    tripId: event.tripId,
    tripTitle: parentTrip?.title || '未命名行程',
    title: event.title,
    timeLabel: eventTimeRange(event),
    locationName: event.locationName || '',
    icon: eventIconName(event),
    tone: 'event',
    sort: new Date(event.startAt).getTime(),
  }
}

const isUpcomingTrip = (item: Trip) => {
  if (!item.startDate || ['completed', 'canceled', 'archived'].includes(item.status)) return false
  return parseDate(item.startDate).getTime() >= parseDate(today).getTime()
}

const isDateInsideTrip = (date: string, item: Trip) => {
  if (!item.startDate) return false
  const end = item.endDate || item.startDate
  return date >= item.startDate && date <= end
}

const eachDate = (start: string, end: string) => {
  const result: string[] = []
  let cursor = parseDate(start)
  const endDate = parseDate(end)
  while (cursor.getTime() <= endDate.getTime()) {
    result.push(formatDate(cursor))
    cursor = addDays(cursor, 1)
  }
  return result
}

const formatDateRange = (start: string | null, end: string | null) => {
  if (start && end && start !== end) return `${start.replace(/-/g, '/')} - ${end.replace(/-/g, '/')}`
  if (start) return start.replace(/-/g, '/')
  return '日期未定'
}

const compactRangeLabel = (item: Trip | null) => {
  if (!item?.startDate) return '日期未定'
  const start = compactDateLabel(item.startDate)
  const end = compactDateLabel(item.endDate || item.startDate)
  return start === end ? start : `${start} - ${end}`
}

function compactDateLabel(date: string) {
  const d = parseDate(date)
  return `${d.getMonth() + 1}月${d.getDate()}日`
}

function datePart(iso: string) {
  return formatDate(new Date(iso))
}
function formatEventTime(iso: string) {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function todayKey() {
  return formatDate(new Date())
}
function parseDate(date: string) {
  return new Date(`${date}T00:00:00`)
}
function monthStart(date: Date) {
  return new Date(date.getFullYear(), date.getMonth(), 1)
}
function addDays(date: Date, amount: number) {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + amount)
}
function formatDate(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
function isSameMonth(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth()
}

onMounted(loadCalendar)
onShow(loadCalendar)
</script>

<style lang="scss">
.page {
  min-height: 100vh;
  padding: 36rpx $candy-gutter 380rpx;
  padding-bottom: calc(380rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: $candy-space-md;
  background:
    radial-gradient(circle at 14% 2%, rgba(224, 64, 160, 0.13), transparent 34%),
    radial-gradient(circle at 92% 20%, rgba(0, 150, 204, 0.11), transparent 28%),
    $candy-background;
}
.topbar {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding-top: $candy-space-xs;
}
.brand {
  display: block;
  font-size: 50rpx;
  font-weight: 800;
  color: $candy-on-background;
  line-height: 1.1;
}
.subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: $candy-font-body-md;
  color: $candy-on-surface-variant;
}
.today-btn {
  margin: 0;
  min-width: 104rpx;
  height: 62rpx;
  line-height: 62rpx;
  padding: 0 24rpx;
  border-radius: $candy-radius-full;
  background: $candy-primary-fixed;
  color: $candy-primary;
  font-size: $candy-font-label-md;
  font-weight: 800;
}
.today-btn::after,
.month-btn::after,
.day-panel__action::after {
  border: none;
}
.login-panel,
.calendar-card,
.day-panel {
  border-radius: $candy-radius-md;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: $candy-shadow-card;
}
.login-panel {
  min-height: 520rpx;
  padding: $candy-space-md;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $candy-space-sm;
  text-align: center;
}
.login-mark {
  width: 104rpx;
  height: 104rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-primary;
  font-size: 58rpx;
  background: $candy-primary-fixed;
}
.login-title {
  font-size: 38rpx;
  font-weight: 800;
  color: $candy-on-surface;
}
.login-hint,
.login-error {
  font-size: $candy-font-body-md;
}
.login-hint {
  color: $candy-on-surface-variant;
}
.login-btn {
  width: 100%;
  margin-top: $candy-space-xs;
}
.calendar-content {
  display: flex;
  flex-direction: column;
  gap: $candy-space-md;
  padding-bottom: 48rpx;
}
.calendar-card {
  padding: 26rpx;
}
.month-head {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $candy-space-sm;
}
.month-title {
  font-size: 40rpx;
  font-weight: 900;
  color: $candy-on-surface;
}
.month-btn {
  margin: 0;
  width: 68rpx;
  height: 68rpx;
  line-height: 64rpx;
  padding: 0;
  border-radius: 50%;
  background: $candy-primary-fixed;
  color: $candy-primary;
  font-size: 46rpx;
  font-weight: 700;
}
.weekday-row,
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
}
.weekday {
  height: 42rpx;
  text-align: center;
  font-size: 22rpx;
  font-weight: 800;
  color: $candy-on-surface-variant;
}
.calendar-grid {
  gap: 8rpx;
}
.calendar-day {
  min-width: 0;
  aspect-ratio: 1;
  border-radius: 24rpx;
  padding: 10rpx 6rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  color: $candy-on-surface;
  background: rgba(255, 255, 255, 0.54);
  border: 2rpx solid transparent;
}
.calendar-day--muted {
  color: rgba(96, 72, 104, 0.35);
}
.calendar-day--filled {
  background: $candy-surface-container-low;
}
.calendar-day--today {
  border-color: rgba(0, 150, 204, 0.38);
}
.calendar-day--selected {
  color: $candy-on-primary;
  background: $candy-primary;
  box-shadow: $candy-shadow-primary;
}
.calendar-day__num {
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1;
}
.calendar-day__marks {
  height: 24rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}
.calendar-day__trip-mark,
.calendar-day__event-mark {
  min-width: 24rpx;
  height: 24rpx;
  line-height: 24rpx;
  padding: 0 6rpx;
  border-radius: $candy-radius-full;
  text-align: center;
  font-size: 16rpx;
  font-weight: 900;
}
.calendar-day__trip-mark {
  color: $candy-on-tertiary;
  background: $candy-tertiary;
}
.calendar-day__event-mark {
  color: $candy-on-secondary;
  background: $candy-secondary;
}
.calendar-day--selected .calendar-day__trip-mark,
.calendar-day--selected .calendar-day__event-mark {
  color: $candy-primary;
  background: $candy-on-primary;
}
.day-panel {
  padding: 26rpx;
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
}
.day-panel__head {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: $candy-space-sm;
}
.day-panel__date {
  display: block;
  font-size: 34rpx;
  font-weight: 900;
  color: $candy-on-surface;
}
.day-panel__hint {
  display: block;
  margin-top: 4rpx;
  font-size: $candy-font-label-md;
  color: $candy-on-surface-variant;
}
.day-panel__action {
  margin: 0;
  flex: 0 0 148rpx;
  height: 58rpx;
  line-height: 58rpx;
  padding: 0 18rpx;
  border-radius: $candy-radius-full;
  background: $candy-secondary-fixed;
  color: $candy-secondary;
  font-size: $candy-font-label-md;
  font-weight: 800;
}
.timeline-switch {
  padding: 6rpx;
  border-radius: $candy-radius-full;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 6rpx;
  background: $candy-surface-container-low;
}
.timeline-switch__item {
  min-width: 0;
  height: 58rpx;
  border-radius: $candy-radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  font-weight: 800;
}
.timeline-switch__item--active {
  color: $candy-on-primary;
  background: $candy-primary;
  box-shadow: 0 8rpx 18rpx rgba(224, 64, 160, 0.18);
}
.trip-chip-row {
  width: 100%;
  white-space: nowrap;
}
.trip-chip-track {
  display: inline-flex;
  flex-direction: row;
  gap: 10rpx;
  padding-bottom: 2rpx;
}
.trip-chip {
  max-width: 280rpx;
  height: 52rpx;
  padding: 0 22rpx;
  border-radius: $candy-radius-full;
  display: inline-flex;
  align-items: center;
  color: $candy-on-surface-variant;
  background: $candy-surface-container-low;
  font-size: $candy-font-label-md;
  font-weight: 800;
}
.trip-chip text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.trip-chip--active {
  color: $candy-primary;
  background: $candy-primary-fixed;
}
.empty-day {
  min-height: 180rpx;
  border-radius: $candy-radius-md;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  text-align: center;
  background: $candy-surface-container-low;
  color: $candy-on-surface-variant;
}
.empty-day__title {
  color: $candy-on-surface;
  font-size: $candy-font-body-lg;
  font-weight: 800;
}
.empty-day__hint {
  font-size: $candy-font-body-md;
}
.schedule-list {
  display: flex;
  flex-direction: column;
}
.overview-list {
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
}
.overview-group {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}
.overview-group__head {
  padding: 0 8rpx 8rpx;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
}
.overview-group__date {
  color: $candy-on-surface;
  font-size: $candy-font-body-md;
  font-weight: 900;
}
.overview-group__count {
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  font-weight: 700;
}
.schedule-item {
  display: grid;
  grid-template-columns: 92rpx 54rpx 1fr;
  min-height: 112rpx;
}
.schedule-item__time {
  padding-top: 18rpx;
  color: $candy-primary;
  font-size: 22rpx;
  font-weight: 900;
}
.schedule-item__rail {
  position: relative;
  display: flex;
  justify-content: center;
}
.schedule-item__rail::before {
  content: '';
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4rpx;
  border-radius: 4rpx;
  background: $candy-outline-variant;
}
.schedule-item__dot {
  position: relative;
  z-index: 1;
  width: 48rpx;
  height: 48rpx;
  margin-top: 12rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $candy-primary;
  font-size: 28rpx;
  background: $candy-primary-fixed;
  box-shadow: 0 0 0 8rpx #ffffff;
}
.schedule-item--trip .schedule-item__dot {
  color: $candy-tertiary;
  background: $candy-tertiary-fixed;
}
.schedule-item__body {
  min-width: 0;
  margin: 0 0 18rpx 8rpx;
  padding: 18rpx 20rpx;
  border-radius: 28rpx;
  background: $candy-surface-container-lowest;
  box-shadow: 0 8rpx 20rpx rgba(96, 72, 104, 0.07);
}
.schedule-item__trip {
  display: block;
  color: $candy-on-surface-variant;
  font-size: 22rpx;
  font-weight: 700;
}
.schedule-item__title {
  display: block;
  margin-top: 4rpx;
  color: $candy-on-surface;
  font-size: $candy-font-body-lg;
  font-weight: 900;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.schedule-item__meta {
  display: block;
  margin-top: 6rpx;
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
}
</style>
