<template>
  <view class="page">
    <view class="editor-top">
      <text class="brand">Candy Travel</text>
      <text class="editor-label">{{ editorLabel }}</text>
    </view>

    <view class="trip-hero">
      <text class="hero-kicker">下一站去哪？</text>
      <view class="title-row">
        <text class="pin">📍</text>
        <input
          class="title-input"
          v-model="form.title"
          placeholder="给这次旅行起个名字"
          confirm-type="done"
        />
      </view>
    </view>

    <!-- 如何抵达？ -->
    <view class="section transport-section">
      <view class="section-head">
        <text class="section-emoji">🛫</text>
        <text class="section-title">如何抵达？</text>
      </view>
      <view class="mode-grid">
        <view
          v-for="m in modes"
          :key="m.value"
          class="mode-cell"
          :class="{ 'mode-cell--active': form.transportMode === m.value }"
          @click="form.transportMode = m.value"
        >
          <text class="mode-icon">{{ m.icon }}</text>
          <text class="mode-label">{{ m.label }}</text>
        </view>
      </view>
    </view>

    <!-- 行程日期 -->
    <view class="date-row">
      <view class="candy-card time-card">
        <text class="time-label">出发日期</text>
        <view class="time-control">
          <text class="time-icon">📅</text>
          <picker
            mode="date"
            :value="form.departDate"
            @change="onDepartDateChange"
            class="time-picker"
          >
            <text class="time-value">{{ form.departDate || '选择日期' }}</text>
          </picker>
        </view>
      </view>
      <view class="candy-card time-card">
        <text class="time-label">结束日期</text>
        <view class="time-control">
          <text class="time-icon">🏁</text>
          <picker
            mode="date"
            :value="form.endDate"
            :start="form.departDate || undefined"
            @change="onEndDateChange"
            class="time-picker"
          >
            <text class="time-value">{{ form.endDate || '选择日期' }}</text>
          </picker>
        </view>
      </view>
    </view>

    <!-- 出发时间 -->
    <view class="time-row">
      <view class="candy-card time-card time-card--wide">
        <text class="time-label">出发时间</text>
        <view class="time-control">
          <text class="time-icon">🕐</text>
          <picker
            mode="time"
            :value="form.departTime"
            @change="onDepartTimeChange"
            class="time-picker"
          >
            <text class="time-value">{{ form.departTime || '选择时间' }}</text>
          </picker>
        </view>
      </view>
    </view>

    <!-- 每日行程 -->
    <view class="section">
      <view class="section-head section-head--split">
        <view class="section-title-row">
          <text class="section-emoji">🧭</text>
          <text class="section-title">每日行程</text>
        </view>
        <button
          class="mini-action"
          :disabled="!tripId"
          @click="onShowEventAdd"
        >
          ＋ 添加事件
        </button>
      </view>

      <view class="candy-card event-panel">
        <view v-if="!tripId" class="empty-events">
          <text class="empty-events__title">保存行程后可添加事件</text>
          <text class="empty-events__hint">选择图标，记录任意安排</text>
        </view>
        <view v-else-if="eventLoading" class="empty-events">
          <text class="empty-events__hint">加载行程事件...</text>
        </view>
        <view v-else-if="eventGroups.length === 0" class="empty-events">
          <text class="empty-events__title">还没有具体行程</text>
          <text class="empty-events__hint">添加当天要做的事、预约或地点</text>
        </view>
        <view v-else class="event-groups">
          <view
            v-for="group in eventGroups"
            :key="group.date"
            class="event-day"
          >
            <view class="event-day__head">
              <text class="event-day__date">{{ formatEventDate(group.date) }}</text>
              <text class="event-day__count">{{ group.events.length }} 项</text>
            </view>
            <view
              v-for="event in group.events"
              :key="event.id"
              class="event-card"
              @click="onEditEvent(event)"
            >
              <view class="event-icon-badge">
                <text>{{ eventIcon(event) }}</text>
              </view>
              <view class="event-body">
                <text class="event-title">{{ event.title }}</text>
                <text class="event-time">{{ eventTimeRange(event) }}</text>
                <text v-if="event.locationName" class="event-meta">📍 {{ event.locationName }}</text>
                <text v-if="event.note" class="event-meta">{{ event.note }}</text>
              </view>
              <button v-if="canDeleteEvent(event)" class="event-delete" @click.stop="onDeleteEvent(event.id)">×</button>
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 准备好了吗？检查清单 -->
    <view class="section">
      <view class="section-head">
        <text class="section-emoji">✓</text>
        <text class="section-title">准备好了吗？</text>
      </view>
      <view class="candy-card checklist">
        <view v-if="!tripId" class="empty-checklist">
          <text class="candy-text-muted">保存行程后可编辑检查清单</text>
        </view>
        <view v-else-if="checklistItems.length === 0" class="empty-checklist">
          <text class="candy-text-muted">暂无检查项</text>
        </view>
        <view
          v-for="item in checklistItems"
          :key="item.id"
          class="checklist-row"
          @click="toggleChecked(item)"
        >
          <view class="check-box" :class="{ 'check-box--on': item.checked }">
            <text v-if="item.checked" class="check-mark">✓</text>
          </view>
          <text class="check-label" :class="{ 'check-label--done': item.checked }">{{ item.label }}</text>
          <text class="check-cat">{{ catLabels[item.category] }}</text>
          <button class="check-delete" @click.stop="onDeleteChecklistItem(item)">×</button>
        </view>

        <button
          class="candy-btn candy-btn--ghost add-btn"
          :disabled="!tripId"
          @click="onShowAdd"
        >
          {{ tripId ? '＋ 添加检查项' : '保存后添加检查项' }}
        </button>
      </view>
    </view>

    <!-- 旅行笔记 -->
    <view class="candy-card section">
      <view class="section-head">
        <text class="section-emoji">📝</text>
        <text class="section-title">旅行笔记</text>
      </view>
      <textarea
        class="note-input"
        v-model="form.note"
        placeholder="留点提醒给自己，比如预约代码、路线、感想……"
        :auto-height="true"
      />
    </view>

    <!-- 保存 -->
    <button
      class="candy-btn candy-btn--primary save-btn"
      :disabled="saving || deleting"
      @click="onSave"
    >
      <text class="save-icon">☁︎</text>
      <text>{{ saving ? '保存中…' : '保存计划' }}</text>
    </button>

    <button
      v-if="tripId"
      class="delete-btn"
      :disabled="saving || deleting"
      @click="onDelete"
    >
      {{ deleting ? '删除中…' : '删除这次旅行' }}
    </button>

    <CandyBottomNav :before-navigate="confirmLeaveIfDirty" />

    <!-- 添加事件弹层 -->
    <view v-if="eventAddOpen" class="modal-mask" @click="eventAddOpen = false">
      <view class="modal" @click.stop>
        <text class="modal-title">{{ eventEditingId ? '编辑事件' : '添加事件' }}</text>
        <text class="modal-field-label">选择图标</text>
        <view class="event-icon-grid">
          <view
            v-for="icon in eventIcons"
            :key="icon"
            class="event-icon-choice"
            :class="{ 'event-icon-choice--active': eventForm.icon === icon }"
            @click="eventForm.icon = icon"
          >
            <text>{{ icon }}</text>
          </view>
        </view>
        <input
          class="candy-input modal-input"
          v-model="eventForm.title"
          placeholder="事件名称，例如：在樱屋吃午餐"
        />
        <view class="event-form-row">
          <view class="event-form-cell">
            <text class="modal-field-label">日期</text>
            <picker
              mode="date"
              :value="eventForm.date"
              :start="form.departDate || undefined"
              :end="form.endDate || undefined"
              @change="onEventDateChange"
            >
              <text class="event-picker-value">{{ eventForm.date || '选择日期' }}</text>
            </picker>
          </view>
          <view class="event-form-cell">
            <text class="modal-field-label">开始</text>
            <picker
              mode="time"
              :value="eventForm.startTime"
              @change="onEventStartTimeChange"
            >
              <text class="event-picker-value">{{ eventForm.startTime || '选择时间' }}</text>
            </picker>
          </view>
          <view class="event-form-cell">
            <text class="modal-field-label">结束</text>
            <picker
              mode="time"
              :value="eventForm.endTime"
              @change="onEventEndTimeChange"
            >
              <text class="event-picker-value">{{ eventForm.endTime || '可选' }}</text>
            </picker>
          </view>
        </view>
        <input
          class="candy-input modal-input"
          v-model="eventForm.locationName"
          placeholder="地点，例如：东京国立博物馆"
        />
        <textarea
          class="note-input event-note-input"
          v-model="eventForm.note"
          placeholder="备注，可选"
          :auto-height="true"
        />
        <view class="modal-actions">
          <button class="candy-btn candy-btn--ghost" @click="eventAddOpen = false">取消</button>
          <button class="candy-btn candy-btn--primary" :disabled="!eventForm.title" @click="onEventAddSubmit">
            {{ eventEditingId ? '保存事件' : '加入行程' }}
          </button>
        </view>
      </view>
    </view>

    <!-- 添加检查项弹层 -->
    <view v-if="addOpen" class="modal-mask" @click="addOpen = false">
      <view class="modal" @click.stop>
        <text class="modal-title">添加检查项</text>
        <input
          class="candy-input modal-input"
          v-model="addLabel"
          placeholder="名称，例如：墨镜"
        />
        <view class="cat-row">
          <text
            v-for="(label, key) in catLabels"
            :key="key"
            class="cat-tag"
            :class="{ 'cat-tag--active': addCategory === key }"
            @click="addCategory = key"
          >
            {{ label }}
          </text>
        </view>
        <view class="modal-actions">
          <button class="candy-btn candy-btn--ghost" @click="addOpen = false">取消</button>
          <button class="candy-btn candy-btn--primary" :disabled="!addLabel" @click="onAddSubmit">
            加入清单
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { onBackPress, onLoad, onShow } from '@dcloudio/uni-app'

import CandyBottomNav from '../../components/CandyBottomNav.vue'
import type { TransportMode, TripDetail } from '../../services/trip'
import { tripApi } from '../../services/trip'
import {
  CATEGORY_LABELS as catLabels,
  type ChecklistCategory,
  type ChecklistItem,
  checklistApi,
} from '../../services/checklist'
import {
  tripEventApi,
  type TripEvent,
} from '../../services/trip-event'

const tripId = ref<string>('')
const trip = ref<TripDetail | null>(null)
const checklistItems = ref<ChecklistItem[]>([])
const tripEvents = ref<TripEvent[]>([])

const saving = ref(false)
const deleting = ref(false)
const addOpen = ref(false)
const addLabel = ref('')
const addCategory = ref<ChecklistCategory>('other')
const pristineSnapshot = ref('')
const allowLeave = ref(false)
const eventLoading = ref(false)
const eventAddOpen = ref(false)
const eventEditingId = ref<string>('')

interface EventFormState {
  icon: string
  title: string
  date: string
  startTime: string
  endTime: string
  locationName: string
  note: string
}

interface FormState {
  title: string
  transportMode: TransportMode
  departDate: string
  endDate: string
  departTime: string
  note: string
}

const form = reactive<FormState>({
  title: '',
  transportMode: 'flight',
  departDate: '',
  endDate: '',
  departTime: '',
  note: '',
})

const editorLabel = computed(() => (tripId.value ? 'Trip Editor' : 'New Trip'))

const eventIcons = [
  '🏨', '✈️', '🚄', '🚌', '🚗', '🚕', '🚢',
  '🍽️', '☕', '🍰', '🎣', '🏖️', '🏛️', '🌿',
  '🛍️', '🎫', '📸', '💆', '🧳', '📌', '⏰', '✨',
]

const eventForm = reactive<EventFormState>({
  icon: '📌',
  title: '',
  date: '',
  startTime: '',
  endTime: '',
  locationName: '',
  note: '',
})

const eventGroups = computed(() => {
  const groups = new Map<string, TripEvent[]>()
  const sorted = [...tripEvents.value].sort((a, b) => (
    new Date(a.startAt).getTime() - new Date(b.startAt).getTime() || a.sortOrder - b.sortOrder
  ))
  sorted.forEach((event) => {
    const date = datePart(event.startAt)
    const list = groups.get(date) || []
    list.push(event)
    groups.set(date, list)
  })
  return [...groups.entries()].map(([date, events]) => ({ date, events }))
})

const modes: Array<{ value: TransportMode; icon: string; label: string }> = [
  { value: 'flight', icon: '✈️', label: '飞机' },
  { value: 'train', icon: '🚄', label: '火车' },
  { value: 'bus', icon: '🚌', label: '巴士' },
  { value: 'car', icon: '🚗', label: '自驾' },
]

onLoad((opts?: Record<string, string | undefined>) => {
  if (opts?.id) {
    tripId.value = opts.id
    void load()
  } else {
    initNewTrip()
  }
})

onShow(() => {
  if (tripId.value && !hasUnsavedChanges()) void load()
})

onBackPress(() => {
  if (allowLeave.value || !hasUnsavedChanges()) return false
  void confirmLeaveIfDirty().then((ok) => {
    if (!ok) return
    allowLeave.value = true
    uni.navigateBack()
  })
  return true
})

const load = async () => {
  try {
    trip.value = await tripApi.get(tripId.value)
    syncFormFromTrip(trip.value)
    checklistItems.value = await checklistApi.list(tripId.value)
    await loadEvents()
    markPristine()
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

const loadEvents = async () => {
  if (!tripId.value) return
  eventLoading.value = true
  try {
    tripEvents.value = await tripEventApi.list(tripId.value)
  } catch {
    uni.showToast({ title: '行程事件加载失败', icon: 'none' })
  } finally {
    eventLoading.value = false
  }
}

const initNewTrip = () => {
  tripId.value = ''
  trip.value = null
  checklistItems.value = []
  tripEvents.value = []
  form.title = '新的旅行'
  form.transportMode = 'flight'
  form.departDate = ''
  form.endDate = ''
  form.departTime = ''
  form.note = ''
  markPristine()
}

const syncFormFromTrip = (t: TripDetail) => {
  form.title = t.title
  form.transportMode = 'flight'
  form.departDate = ''
  form.endDate = ''
  form.departTime = ''
  form.note = t.note || ''
  if (t.summary.transport) {
    form.transportMode = (t.summary.transport.mode as TransportMode) || 'flight'
    const d = t.summary.transport.departAt
    if (d) {
      const dt = new Date(d)
      form.departDate = formatDate(dt)
      form.departTime = formatTime(dt)
    }
  } else if (t.startDate) {
    form.departDate = t.startDate
  }
  form.endDate = t.endDate || ''
}

const formSnapshot = () => JSON.stringify({
  title: form.title,
  transportMode: form.transportMode,
  departDate: form.departDate,
  endDate: form.endDate,
  departTime: form.departTime,
  note: form.note,
})

const markPristine = () => {
  pristineSnapshot.value = formSnapshot()
}

const hasUnsavedChanges = () => pristineSnapshot.value !== formSnapshot()

const formatDate = (d: Date) => d.toISOString().slice(0, 10)
const formatTime = (d: Date) => d.toTimeString().slice(0, 5)
const datePart = (iso: string) => {
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const formatEventDate = (date: string) => {
  const [, month, day] = date.split('-')
  return `${Number(month)}月${Number(day)}日`
}

const formatEventTime = (iso: string) => {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const eventIcon = (event: TripEvent) => {
  if (typeof event.meta?.icon === 'string' && event.meta.icon) return event.meta.icon
  if (event.eventType === 'transport') {
    const mode = event.meta?.mode
    return ({ flight: '✈️', train: '🚄', bus: '🚌', car: '🚗' }[String(mode)] || '✈️')
  }
  return ({ stay: '🏨', activity: '📌', reminder: '⏰' }[event.eventType] || '📌')
}

const eventTimeRange = (event: TripEvent) => {
  const start = formatEventTime(event.startAt)
  if (!event.endAt) return start
  return `${start} - ${formatEventTime(event.endAt)}`
}

const canDeleteEvent = (event: TripEvent) => Boolean(event.meta?.icon) || ['activity', 'reminder'].includes(event.eventType)
const canEditEvent = canDeleteEvent

const onDepartDateChange = (e: any) => {
  form.departDate = e.detail.value
  if (form.endDate && form.endDate < form.departDate) {
    form.endDate = form.departDate
  }
}
const onEndDateChange = (e: any) => {
  form.endDate = e.detail.value
}
const onDepartTimeChange = (e: any) => {
  form.departTime = e.detail.value
}

const buildIsoDateTime = (date: string, time: string): string | null => {
  if (!date) return null
  const t = time || '00:00'
  // 让小程序按本地（trip.timezone）解释；后端按 trip.timezone 渲染
  return new Date(`${date}T${t}:00`).toISOString()
}

const onSave = async () => {
  await saveTrip()
}

const saveTrip = async (options: { redirectNew?: boolean } = {}): Promise<boolean> => {
  const redirectNew = options.redirectNew ?? true
  if (!form.title.trim()) {
    uni.showToast({ title: '请填写行程名', icon: 'none' })
    return false
  }
  if (form.endDate && !form.departDate) {
    uni.showToast({ title: '请先选择出发日期', icon: 'none' })
    return false
  }
  if (form.departDate && form.endDate && form.endDate < form.departDate) {
    uni.showToast({ title: '结束日期不能早于出发日期', icon: 'none' })
    return false
  }
  saving.value = true
  try {
    const wasNewTrip = !tripId.value
    const departIso = buildIsoDateTime(form.departDate, form.departTime)

    const payload: any = {
      title: form.title.trim(),
      note: form.note ? form.note.trim() : null,
      status: 'planning',
    }

    if (form.departDate || form.transportMode) {
      payload.transport = {
        mode: form.transportMode,
        departAt: departIso,
        arriveAt: null,
      }
    }
    if (form.departDate) {
      payload.startDate = form.departDate
    }
    payload.endDate = form.endDate || null

    if (wasNewTrip) {
      const created = await tripApi.create({
        title: payload.title,
        note: payload.note,
        startDate: payload.startDate,
        endDate: payload.endDate,
      })
      tripId.value = created.id
    }

    trip.value = await tripApi.patchSummary(tripId.value, payload)
    if (wasNewTrip) {
      checklistItems.value = await checklistApi.list(tripId.value)
      tripEvents.value = []
    }
    markPristine()
    uni.showToast({ title: '已保存', icon: 'success' })
    if (wasNewTrip && redirectNew) {
      allowLeave.value = true
      uni.redirectTo({ url: `/pages/edit/index?id=${tripId.value}` })
    }
    return true
  } catch (e) {
    uni.showToast({ title: '保存失败', icon: 'none' })
    return false
  } finally {
    saving.value = false
  }
}

const confirmLeaveIfDirty = async (): Promise<boolean> => {
  if (allowLeave.value || !hasUnsavedChanges()) return true
  return new Promise((resolve) => {
    uni.showModal({
      title: '保存更改？',
      content: '当前行程有未保存的修改，是否先保存再离开？',
      cancelText: '不保存',
      confirmText: '保存',
      confirmColor: '#e040a0',
      success: (res) => {
        if (!res.confirm) {
          allowLeave.value = true
          resolve(true)
          return
        }
        void saveTrip({ redirectNew: false }).then((ok) => {
          if (ok) allowLeave.value = true
          resolve(ok)
        })
      },
      fail: () => resolve(false),
    })
  })
}

const onDelete = () => {
  if (!tripId.value || deleting.value) return
  uni.showModal({
    title: '删除旅程',
    content: '删除后这次旅行会从列表中移除，确定要继续吗？',
    confirmText: '删除',
    confirmColor: '#ba1a1a',
    success: (res) => {
      if (res.confirm) void deleteTrip()
    },
  })
}

const deleteTrip = async () => {
  deleting.value = true
  try {
    await tripApi.delete(tripId.value)
    allowLeave.value = true
    uni.showToast({ title: '已删除', icon: 'success' })
    uni.redirectTo({ url: '/pages/index/index' })
  } catch {
    uni.showToast({ title: '删除失败', icon: 'none' })
  } finally {
    deleting.value = false
  }
}

const resetEventForm = () => {
  eventEditingId.value = ''
  eventForm.icon = '📌'
  eventForm.title = ''
  eventForm.date = form.departDate || datePart(new Date().toISOString())
  eventForm.startTime = ''
  eventForm.endTime = ''
  eventForm.locationName = ''
  eventForm.note = ''
}

const onShowEventAdd = async () => {
  if (!tripId.value) {
    uni.showToast({ title: '请先保存行程', icon: 'none' })
    return
  }
  if (!form.departDate) {
    uni.showToast({ title: '请先设置出发日期', icon: 'none' })
    return
  }
  if (hasUnsavedChanges()) {
    uni.showModal({
      title: '先保存行程？',
      content: '添加事件前需要保存当前行程日期和标题。',
      confirmText: '保存',
      confirmColor: '#e040a0',
      success: (res) => {
        if (!res.confirm) return
        void saveTrip({ redirectNew: false }).then((ok) => {
          if (!ok) return
          resetEventForm()
          eventAddOpen.value = true
        })
      },
    })
    return
  }
  resetEventForm()
  eventAddOpen.value = true
}

const onEditEvent = (event: TripEvent) => {
  if (!canEditEvent(event)) {
    uni.showToast({ title: '交通信息请在上方修改', icon: 'none' })
    return
  }
  eventEditingId.value = event.id
  eventForm.icon = eventIcon(event)
  eventForm.title = event.title
  eventForm.date = datePart(event.startAt)
  eventForm.startTime = formatEventTime(event.startAt)
  eventForm.endTime = event.endAt ? formatEventTime(event.endAt) : ''
  eventForm.locationName = event.locationName || ''
  eventForm.note = event.note || ''
  eventAddOpen.value = true
}

const onEventDateChange = (e: any) => {
  eventForm.date = e.detail.value
}

const onEventStartTimeChange = (e: any) => {
  eventForm.startTime = e.detail.value
}

const onEventEndTimeChange = (e: any) => {
  eventForm.endTime = e.detail.value
}

const validateEventForm = () => {
  if (!eventForm.title.trim()) return '请填写事件名称'
  if (!eventForm.date) return '请选择日期'
  if (!eventForm.startTime) return '请选择开始时间'
  const tripEnd = form.endDate || form.departDate
  if (form.departDate && eventForm.date < form.departDate) return '事件日期不能早于出发日期'
  if (tripEnd && eventForm.date > tripEnd) return '事件日期不能晚于结束日期'
  if (eventForm.endTime && eventForm.endTime < eventForm.startTime) return '结束时间不能早于开始时间'
  return ''
}

const onEventAddSubmit = async () => {
  const error = validateEventForm()
  if (error) {
    uni.showToast({ title: error, icon: 'none' })
    return
  }
  const startAt = buildIsoDateTime(eventForm.date, eventForm.startTime)
  if (!startAt) return
  const endAt = eventForm.endTime ? buildIsoDateTime(eventForm.date, eventForm.endTime) : null
  try {
    if (eventEditingId.value) {
      const updated = await tripEventApi.patch(eventEditingId.value, {
        title: eventForm.title.trim(),
        startAt,
        endAt,
        locationName: eventForm.locationName.trim() || null,
        note: eventForm.note.trim() || null,
        meta: { icon: eventForm.icon },
      })
      tripEvents.value = tripEvents.value.map((event) => (
        event.id === updated.id ? updated : event
      ))
      eventAddOpen.value = false
      eventEditingId.value = ''
      uni.showToast({ title: '已保存', icon: 'success' })
      return
    }

    const created = await tripEventApi.create(tripId.value, {
      eventType: 'activity',
      title: eventForm.title.trim(),
      startAt,
      endAt,
      locationName: eventForm.locationName.trim() || null,
      note: eventForm.note.trim() || null,
      meta: { icon: eventForm.icon },
      status: 'confirmed',
      sortOrder: tripEvents.value.length,
    })
    tripEvents.value.push(created)
    eventAddOpen.value = false
    eventEditingId.value = ''
    uni.showToast({ title: '已添加', icon: 'success' })
  } catch {
    uni.showToast({ title: '添加失败', icon: 'none' })
  }
}

const onDeleteEvent = (eventId: string) => {
  uni.showModal({
    title: '删除事件',
    content: '确定从每日行程中移除这个事件吗？',
    confirmText: '删除',
    confirmColor: '#ba1a1a',
    success: (res) => {
      if (!res.confirm) return
      void deleteEvent(eventId)
    },
  })
}

const deleteEvent = async (eventId: string) => {
  try {
    await tripEventApi.delete(eventId)
    tripEvents.value = tripEvents.value.filter((event) => event.id !== eventId)
    uni.showToast({ title: '已删除', icon: 'success' })
  } catch {
    uni.showToast({ title: '删除失败', icon: 'none' })
  }
}

const toggleChecked = async (item: ChecklistItem) => {
  const next = !item.checked
  item.checked = next  // 乐观更新
  try {
    await checklistApi.patch(item.id, { checked: next })
  } catch {
    item.checked = !next
    uni.showToast({ title: '更新失败', icon: 'none' })
  }
}

const onDeleteChecklistItem = (item: ChecklistItem) => {
  uni.showModal({
    title: '移除检查项',
    content: `确定移除「${item.label}」吗？`,
    confirmText: '移除',
    confirmColor: '#ba1a1a',
    success: (res) => {
      if (!res.confirm) return
      void deleteChecklistItem(item.id)
    },
  })
}

const deleteChecklistItem = async (itemId: string) => {
  try {
    await checklistApi.delete(itemId)
    checklistItems.value = checklistItems.value.filter((item) => item.id !== itemId)
    uni.showToast({ title: '已移除', icon: 'success' })
  } catch {
    uni.showToast({ title: '移除失败', icon: 'none' })
  }
}

const onShowAdd = () => {
  if (!tripId.value) {
    uni.showToast({ title: '请先保存行程', icon: 'none' })
    return
  }
  addLabel.value = ''
  addCategory.value = 'other'
  addOpen.value = true
}

const onAddSubmit = async () => {
  if (!addLabel.value.trim()) return
  try {
    const created = await checklistApi.create(tripId.value, {
      label: addLabel.value.trim(),
      category: addCategory.value,
    })
    checklistItems.value.push(created)
    addOpen.value = false
  } catch (e) {
    uni.showToast({ title: '加入失败', icon: 'none' })
  }
}
</script>

<style lang="scss">
.page {
  padding: $candy-space-md $candy-gutter 220rpx;
  padding-bottom: calc(220rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: $candy-space-md;
  min-height: 100vh;
  background:
    radial-gradient(circle at 10% 2%, rgba(224, 64, 160, 0.14), transparent 32%),
    radial-gradient(circle at 92% 16%, rgba(0, 150, 204, 0.1), transparent 28%),
    $candy-background;
}
.editor-top {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  justify-content: space-between;
  padding-top: 4rpx;
}
.brand {
  font-size: 34rpx;
  font-weight: 900;
  color: $candy-primary;
}
.editor-label {
  padding: 8rpx 18rpx;
  border-radius: $candy-radius-full;
  background: $candy-surface-container-lowest;
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  font-weight: 700;
  box-shadow: $candy-shadow-card;
}
.trip-hero {
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
  padding: 34rpx;
  border-radius: $candy-radius-lg;
  background: $candy-primary;
  color: $candy-on-primary;
  box-shadow: $candy-shadow-primary;
}
.hero-kicker {
  font-size: $candy-font-label-md;
  font-weight: 800;
  opacity: 0.9;
}

.section {
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
}
.section-head {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: $candy-space-xs;
}
.section-head--split {
  justify-content: space-between;
}
.section-title-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: $candy-space-xs;
}
.section-emoji {
  font-size: 32rpx;
}
.section-title {
  font-size: $candy-font-body-lg;
  font-weight: 700;
  color: $candy-on-surface;
}
.section-title--primary {
  color: $candy-primary;
}

/* 标题输入 */
.title-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: $candy-space-xs;
  background: $candy-surface-container-lowest;
  border-radius: $candy-radius-full;
  padding: 18rpx $candy-space-sm;
  border: 0;
}
.pin {
  font-size: 36rpx;
}
.title-input {
  flex: 1;
  font-size: $candy-font-body-lg;
  color: $candy-on-surface;
  background: transparent;
}

/* 出行方式 */
.transport-section .section-head {
  padding: 0 4rpx;
}
.mode-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $candy-space-sm;
}
.mode-cell {
  background: $candy-surface-container-lowest;
  border-radius: $candy-radius-lg;
  padding: $candy-space-sm $candy-space-xs;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
  border: 4rpx solid transparent;
  box-shadow: $candy-shadow-card;
}
.mode-cell--active {
  background: $candy-primary-fixed;
  border-color: $candy-primary;
  box-shadow: $candy-shadow-primary;
}
.mode-icon {
  font-size: 56rpx;
}
.mode-label {
  font-size: $candy-font-body-md;
  color: $candy-on-surface;
  font-weight: 600;
}

/* 行程日期 / 出发时间 */
.date-row,
.time-row {
  display: flex;
  flex-direction: row;
  gap: $candy-space-sm;
}
.time-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: $candy-space-xs;
  padding: $candy-space-sm;
  background: $candy-secondary-fixed;
  border-radius: $candy-radius-md;
}
.time-card--wide {
  background: $candy-primary-fixed;
}
.time-label {
  font-size: $candy-font-label-md;
  font-weight: 600;
  color: $candy-secondary;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.time-control {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: $candy-space-xs;
}
.time-icon {
  font-size: 32rpx;
}
.time-picker {
  flex: 1;
}
.time-value {
  font-size: $candy-font-headline-md;
  font-weight: 700;
  color: $candy-on-surface;
}

/* 每日行程 */
.mini-action {
  margin: 0;
  min-width: 156rpx;
  height: 58rpx;
  line-height: 58rpx;
  padding: 0 20rpx;
  border-radius: $candy-radius-full;
  background: $candy-primary;
  color: $candy-on-primary;
  font-size: $candy-font-label-md;
  font-weight: 700;
  box-shadow: 0 8rpx 20rpx rgba(224, 64, 160, 0.18);
}
.mini-action::after {
  border: none;
}
.mini-action[disabled] {
  background: $candy-outline-variant;
  color: $candy-on-surface-variant;
  box-shadow: none;
}
.event-panel {
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
  padding: 20rpx;
  background: rgba(255, 255, 255, 0.82);
}
.empty-events {
  min-height: 168rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  text-align: center;
  border-radius: $candy-radius-md;
  background: $candy-surface-container-low;
}
.empty-events__title {
  font-size: $candy-font-body-lg;
  font-weight: 800;
  color: $candy-on-surface;
}
.empty-events__hint {
  font-size: $candy-font-body-md;
  color: $candy-on-surface-variant;
}
.event-groups {
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
}
.event-day {
  display: flex;
  flex-direction: column;
  gap: $candy-space-xs;
}
.event-day__head {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: 0 8rpx;
}
.event-day__date {
  font-size: $candy-font-body-md;
  font-weight: 800;
  color: $candy-on-surface;
}
.event-day__count {
  font-size: $candy-font-label-md;
  color: $candy-on-surface-variant;
}
.event-card {
  position: relative;
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  gap: 18rpx;
  padding: 22rpx 58rpx 22rpx 22rpx;
  border-radius: 34rpx;
  background: $candy-surface-container-lowest;
  box-shadow: 0 8rpx 22rpx rgba(96, 72, 104, 0.07);
}
.event-card:active {
  background: $candy-surface-container-low;
}
.event-icon-badge {
  flex: 0 0 64rpx;
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $candy-primary-fixed;
  font-size: 34rpx;
}
.event-body {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}
.event-title {
  min-width: 0;
  color: $candy-on-surface;
  font-size: $candy-font-body-lg;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.event-time {
  color: $candy-primary;
  font-size: $candy-font-label-md;
  font-weight: 800;
}
.event-meta {
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
}
.event-delete {
  position: absolute;
  top: 14rpx;
  right: 14rpx;
  width: 42rpx;
  height: 42rpx;
  line-height: 38rpx;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  color: $candy-on-surface-variant;
  font-size: 32rpx;
}
.event-delete::after {
  border: none;
}

/* 检查清单 */
.checklist {
  display: flex;
  flex-direction: column;
  gap: $candy-space-xs;
  padding: $candy-space-sm;
}
.empty-checklist {
  padding: $candy-space-sm 0;
  text-align: center;
}
.checklist-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: $candy-space-sm;
  padding: 16rpx 8rpx;
  border-radius: $candy-radius-md;
  background: rgba(255, 255, 255, 0.6);
}
.check-box {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  border: 4rpx solid $candy-outline-variant;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $candy-surface-container-lowest;
}
.check-box--on {
  background: $candy-primary;
  border-color: $candy-primary;
}
.check-mark {
  color: $candy-on-primary;
  font-size: 24rpx;
  font-weight: 800;
}
.check-label {
  flex: 1;
  font-size: $candy-font-body-lg;
  color: $candy-on-surface;
}
.check-label--done {
  text-decoration: line-through;
  color: $candy-on-surface-variant;
}
.check-cat {
  flex: 0 0 auto;
  font-size: $candy-font-label-md;
  color: $candy-on-secondary-fixed-variant;
  background: $candy-secondary-fixed;
  padding: 4rpx 16rpx;
  border-radius: $candy-radius-full;
}
.check-delete {
  flex: 0 0 42rpx;
  width: 42rpx;
  height: 42rpx;
  line-height: 38rpx;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  color: $candy-on-surface-variant;
  font-size: 32rpx;
}
.check-delete::after {
  border: none;
}
.add-btn {
  margin-top: $candy-space-xs;
}
.add-btn[disabled] {
  color: $candy-on-surface-variant;
  opacity: 0.58;
}

/* 笔记 */
.note-input {
  width: 100%;
  min-height: 160rpx;
  background: $candy-surface-container-lowest;
  border-radius: $candy-radius-md;
  padding: $candy-space-sm;
  font-size: $candy-font-body-md;
  color: $candy-on-surface;
  line-height: 1.6;
}

/* 保存 */
.save-btn {
  margin-top: $candy-space-sm;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: $candy-space-xs;
}
.save-icon {
  font-size: 32rpx;
}
.delete-btn {
  align-self: center;
  margin-top: 4rpx;
  min-width: 240rpx;
  height: 64rpx;
  line-height: 64rpx;
  border-radius: $candy-radius-full;
  background: transparent;
  color: $candy-error;
  font-size: $candy-font-label-md;
  font-weight: 600;
}
.delete-btn::after {
  border: 2rpx solid rgba(186, 26, 26, 0.18);
  border-radius: $candy-radius-full;
}
.delete-btn[disabled] {
  opacity: 0.55;
}

/* 添加检查项弹层 */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(40, 19, 48, 0.4);
  display: flex;
  align-items: flex-end;
  z-index: 999;
}
.modal {
  width: 100%;
  background: $candy-surface-container-lowest;
  border-top-left-radius: $candy-radius-md;
  border-top-right-radius: $candy-radius-md;
  padding: $candy-space-md;
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
}
.modal-title {
  font-size: $candy-font-headline-md;
  font-weight: 700;
  color: $candy-on-surface;
}
.event-icon-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: $candy-space-xs;
}
.event-icon-choice {
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $candy-surface-container;
  border: 3rpx solid transparent;
  font-size: 34rpx;
}
.event-icon-choice--active {
  background: $candy-primary-fixed;
  border-color: $candy-primary;
  box-shadow: 0 8rpx 20rpx rgba(224, 64, 160, 0.16);
}
.modal-input {
  width: 100%;
}
.modal-field-label {
  font-size: 20rpx;
  font-weight: 800;
  color: $candy-on-surface-variant;
}
.event-form-row {
  display: grid;
  grid-template-columns: 1.2fr 1fr 1fr;
  gap: $candy-space-xs;
}
.event-form-cell {
  min-width: 0;
  padding: 14rpx 16rpx;
  border-radius: $candy-radius-md;
  background: $candy-surface-container-low;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.event-picker-value {
  color: $candy-on-surface;
  font-size: $candy-font-body-md;
  font-weight: 800;
}
.event-note-input {
  min-height: 96rpx;
}
.cat-row {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 12rpx;
}
.cat-tag {
  padding: 8rpx 24rpx;
  border-radius: $candy-radius-full;
  background: $candy-surface-container;
  font-size: $candy-font-label-md;
  color: $candy-on-surface;
}
.cat-tag--active {
  background: $candy-primary;
  color: $candy-on-primary;
}
.modal-actions {
  display: flex;
  flex-direction: row;
  gap: $candy-space-sm;
}
.modal-actions .candy-btn {
  flex: 1;
}
</style>
