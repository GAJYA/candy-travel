<template>
  <view class="page">
    <view class="editor-top">
      <text class="brand">Candy Travel</text>
      <text class="editor-label">Trip Editor</text>
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

    <!-- 出发安排 -->
    <view class="time-row">
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

    <!-- 入住酒店 -->
    <view class="candy-card section stay-card">
      <view class="section-head">
        <text class="section-emoji">🏨</text>
        <text class="section-title">入住酒店</text>
      </view>
      <input
        class="hotel-input"
        v-model="form.hotelName"
        placeholder="酒店名称（可留空表示不入住）"
      />
    </view>

    <!-- 准备好了吗？检查清单 -->
    <view class="section">
      <view class="section-head">
        <text class="section-emoji">✓</text>
        <text class="section-title">准备好了吗？</text>
      </view>
      <view class="candy-card checklist">
        <view v-if="checklistItems.length === 0" class="empty-checklist">
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
        </view>

        <button class="candy-btn candy-btn--ghost add-btn" @click="onShowAdd">
          ＋ 添加检查项
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
      class="delete-btn"
      :disabled="saving || deleting"
      @click="onDelete"
    >
      {{ deleting ? '删除中…' : '删除这次旅行' }}
    </button>

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
import { onLoad, onShow } from '@dcloudio/uni-app'

import type { TransportMode, TripDetail } from '../../services/trip'
import { tripApi } from '../../services/trip'
import {
  CATEGORY_LABELS as catLabels,
  type ChecklistCategory,
  type ChecklistItem,
  checklistApi,
} from '../../services/checklist'

const tripId = ref<string>('')
const trip = ref<TripDetail | null>(null)
const checklistItems = ref<ChecklistItem[]>([])

const saving = ref(false)
const deleting = ref(false)
const addOpen = ref(false)
const addLabel = ref('')
const addCategory = ref<ChecklistCategory>('other')

interface FormState {
  title: string
  transportMode: TransportMode
  departDate: string
  departTime: string
  hotelName: string
  note: string
}

const form = reactive<FormState>({
  title: '',
  transportMode: 'flight',
  departDate: '',
  departTime: '',
  hotelName: '',
  note: '',
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
  }
})

onShow(() => {
  if (tripId.value) void load()
})

const load = async () => {
  try {
    trip.value = await tripApi.get(tripId.value)
    syncFormFromTrip(trip.value)
    checklistItems.value = await checklistApi.list(tripId.value)
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}

const syncFormFromTrip = (t: TripDetail) => {
  form.title = t.title
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
  form.hotelName = t.summary.stay?.hotelName || ''
}

const formatDate = (d: Date) => d.toISOString().slice(0, 10)
const formatTime = (d: Date) => d.toTimeString().slice(0, 5)

const onDepartDateChange = (e: any) => {
  form.departDate = e.detail.value
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
  if (!tripId.value) return
  if (!form.title.trim()) {
    uni.showToast({ title: '请填写行程名', icon: 'none' })
    return
  }
  saving.value = true
  try {
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
    if (form.hotelName.trim()) {
      payload.stay = {
        hotelName: form.hotelName.trim(),
        checkinAt: departIso,
      }
    } else {
      payload.stay = null
    }
    if (form.departDate) {
      payload.startDate = form.departDate
    }

    trip.value = await tripApi.patchSummary(tripId.value, payload)
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (e) {
    uni.showToast({ title: '保存失败', icon: 'none' })
  } finally {
    saving.value = false
  }
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
    uni.showToast({ title: '已删除', icon: 'success' })
    uni.redirectTo({ url: '/pages/index/index' })
  } catch {
    uni.showToast({ title: '删除失败', icon: 'none' })
  } finally {
    deleting.value = false
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

const onShowAdd = () => {
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
  padding: $candy-space-md $candy-gutter 200rpx;
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

/* 出发安排 */
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

/* 酒店 */
.stay-card {
  background: $candy-secondary-fixed;
}
.hotel-input {
  background: $candy-surface-container-lowest;
  border-radius: $candy-radius-full;
  padding: 20rpx $candy-space-sm;
  font-size: $candy-font-body-lg;
  color: $candy-on-surface;
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
  font-size: $candy-font-label-md;
  color: $candy-on-secondary-fixed-variant;
  background: $candy-secondary-fixed;
  padding: 4rpx 16rpx;
  border-radius: $candy-radius-full;
}
.add-btn {
  margin-top: $candy-space-xs;
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
.modal-input {
  width: 100%;
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
