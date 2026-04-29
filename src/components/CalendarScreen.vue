<script setup lang="ts">
import {computed, reactive, ref, watch} from 'vue';
import {Calendar} from 'v-calendar';
import {
  CalendarDays,
  ChevronRight,
  Clock3,
  FilePenLine,
  Landmark,
  MapPin,
  Plane,
  Plus,
  Sparkles,
  Ticket,
  Train,
  Utensils,
  Trash2,
} from 'lucide-vue-next';
import {useTripStore, type TripDay, type TripEvent, type TripEventType} from '@/store/tripStore';

type MarkerKind = 'sparkles' | 'train' | 'dot';
type ClickedDay = {
  date: Date;
};

const {
  tripList,
  selectedTrip,
  selectTrip,
  upsertTripDay,
  removeTripDay,
  upsertTripEvent,
  removeTripEvent,
} = useTripStore();

const today = new Date();
const parseDateOnly = (value: string) => new Date(`${value}T00:00:00`);
const selectedDate = ref(selectedTrip.value ? parseDateOnly(selectedTrip.value.startDate) : new Date());
const calendarKey = ref(0);
const showEventEditor = ref(false);
const editingEventId = ref<string | null>(null);

const formatKey = (date: Date) => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');

  return `${year}-${month}-${day}`;
};

const selectedKey = computed(() => formatKey(selectedDate.value));
const tripFormatter = new Intl.DateTimeFormat('zh-CN', {month: 'numeric', day: 'numeric'});
const timeFormatter = new Intl.DateTimeFormat('zh-CN', {hour: '2-digit', minute: '2-digit', hour12: false});

const dayDraft = reactive({
  summary: '',
  hint: '',
  highlightTag: '',
});

const eventDraft = reactive({
  title: '',
  description: '',
  time: '09:30',
  eventType: 'activity' as TripEventType,
  metaValue: '',
});

const selectedTripDays = computed(() => selectedTrip.value?.days ?? []);
const selectedTripEvents = computed(() => selectedTrip.value?.events ?? []);
const selectedDayRecord = computed<TripDay | null>(() => {
  return selectedTripDays.value.find((day) => day.date === selectedKey.value) ?? null;
});
const selectedDayEvents = computed(() => {
  return selectedTripEvents.value.filter((event) => event.startAt.slice(0, 10) === selectedKey.value);
});
const selectedPlan = computed(() => {
  return {
    summary: selectedDayRecord.value?.summary ?? '今天还没有安排行程',
    hint: selectedDayRecord.value?.hint ?? '可以继续切换月份并点选日期，然后直接为这一天创建新的活动。',
    highlight: selectedDayRecord.value?.highlightTag ?? '空闲',
    activities: selectedDayEvents.value,
  };
});

const selectedDateLabel = computed(() => {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(selectedDate.value);
});

const tripRangeText = computed(() => {
  if (!selectedTrip.value) {
    return '--';
  }

  return `${tripFormatter.format(parseDateOnly(selectedTrip.value.startDate))} - ${tripFormatter.format(parseDateOnly(selectedTrip.value.endDate))}`;
});

const markerMap = computed<Record<string, MarkerKind>>(() => {
  return selectedTripDays.value.reduce<Record<string, MarkerKind>>((accumulator, day) => {
    if (day.highlightTag.includes('出发')) {
      accumulator[day.date] = 'sparkles';
    } else if (day.highlightTag.includes('移动') || day.highlightTag.includes('换城')) {
      accumulator[day.date] = 'train';
    } else {
      accumulator[day.date] = 'dot';
    }
    return accumulator;
  }, {});
});

const travelDayKeys = computed(() => new Set(selectedTripDays.value.map((day) => day.date)));

const calendarMasks = {
  title: 'YYYY年M月',
  weekdays: 'W',
};

const isSameDate = (left: Date, right: Date) =>
  left.getFullYear() === right.getFullYear() &&
  left.getMonth() === right.getMonth() &&
  left.getDate() === right.getDate();

const getMarker = (date: Date) => markerMap.value[formatKey(date)] ?? null;
const isSelected = (date: Date) => isSameDate(date, selectedDate.value);
const isTodayCell = (date: Date) => isSameDate(date, today);
const isTravelDay = (date: Date) => travelDayKeys.value.has(formatKey(date));
const isTravelStart = (date: Date) => selectedTrip.value?.startDate === formatKey(date);

const jumpToToday = () => {
  selectedDate.value = new Date();
  calendarKey.value += 1;
};

const handleDayClick = (day: ClickedDay) => {
  selectedDate.value = day.date;
};

const resetEventDraft = () => {
  editingEventId.value = null;
  eventDraft.title = '';
  eventDraft.description = '';
  eventDraft.time = '09:30';
  eventDraft.eventType = 'activity';
  eventDraft.metaValue = '';
  showEventEditor.value = false;
};

const syncDayDraft = () => {
  dayDraft.summary = selectedDayRecord.value?.summary ?? '今天还没有安排行程';
  dayDraft.hint = selectedDayRecord.value?.hint ?? '可以继续补充交通、活动或住宿安排。';
  dayDraft.highlightTag = selectedDayRecord.value?.highlightTag ?? '空闲';
};

watch([selectedTrip, selectedKey], () => {
  if (selectedTrip.value && !selectedTripDays.value.some((day) => day.date === selectedKey.value)) {
    syncDayDraft();
  } else {
    syncDayDraft();
  }
}, {immediate: true});

watch(
  selectedTrip,
  (trip) => {
    if (trip) {
      selectedDate.value = parseDateOnly(trip.startDate);
    }
  },
  {immediate: true},
);

const saveDayPlan = () => {
  if (!selectedTrip.value) {
    return;
  }

  upsertTripDay(selectedTrip.value.id, {
    id: selectedDayRecord.value?.id,
    date: selectedKey.value,
    summary: dayDraft.summary.trim() || '今天还没有安排行程',
    hint: dayDraft.hint.trim() || '可以继续补充交通、活动或住宿安排。',
    highlightTag: dayDraft.highlightTag.trim() || '空闲',
    sortOrder: selectedDayRecord.value?.sortOrder ?? selectedTripDays.value.length,
  });
};

const deleteDayPlan = () => {
  if (!selectedTrip.value || !selectedDayRecord.value) {
    return;
  }

  removeTripDay(selectedTrip.value.id, selectedDayRecord.value.id);
  resetEventDraft();
};

const openNewEvent = () => {
  editingEventId.value = null;
  eventDraft.title = '';
  eventDraft.description = '';
  eventDraft.time = '09:30';
  eventDraft.eventType = 'activity';
  eventDraft.metaValue = '';
  showEventEditor.value = true;
};

const openEditEvent = (event: TripEvent) => {
  editingEventId.value = event.id;
  eventDraft.title = event.title;
  eventDraft.description = event.description;
  eventDraft.time = event.startAt.slice(11, 16);
  eventDraft.eventType = event.eventType;
  eventDraft.metaValue = event.locationName ?? event.referenceCode ?? '';
  showEventEditor.value = true;
};

const saveEvent = () => {
  if (!selectedTrip.value || !eventDraft.title.trim()) {
    return;
  }

  const tripId = selectedTrip.value.id;
  const startAt = `${selectedKey.value}T${eventDraft.time}:00`;
  const isTransport = eventDraft.eventType === 'transport';

  upsertTripEvent(tripId, {
    id: editingEventId.value ?? undefined,
    eventType: eventDraft.eventType,
    title: eventDraft.title.trim(),
    description: eventDraft.description.trim(),
    startAt: new Date(startAt).toISOString(),
    locationName: isTransport ? undefined : eventDraft.metaValue.trim() || undefined,
    referenceCode: isTransport ? eventDraft.metaValue.trim() || undefined : undefined,
    transportMode: isTransport ? selectedTrip.value.primaryTransportMode : undefined,
    source: 'manual',
    status: 'confirmed',
    meta: {
      tone: isTransport ? 'secondary' : 'tertiary',
      metaIcon: isTransport ? 'ticket' : 'map-pin',
    },
  });

  if (!selectedDayRecord.value) {
    saveDayPlan();
  }

  resetEventDraft();
};

const deleteEvent = (eventId: string) => {
  if (!selectedTrip.value) {
    return;
  }

  removeTripEvent(selectedTrip.value.id, eventId);
  if (editingEventId.value === eventId) {
    resetEventDraft();
  }
};

const formatEventTime = (value: string) => timeFormatter.format(new Date(value));
const getEventMetaLabel = (event: TripEvent) => event.locationName ?? event.referenceCode ?? '待补充';
const getEventTone = (event: TripEvent) => event.meta?.tone === 'secondary' ? 'secondary' : 'tertiary';
const getEventMetaIcon = (event: TripEvent) => event.meta?.metaIcon === 'ticket' ? 'ticket' : 'map-pin';
const getEventCardIcon = (event: TripEvent) => (event.eventType === 'activity' ? 'landmark' : 'utensils');
</script>

<template>
  <div class="space-y-6 pb-24">
    <section class="rounded-3xl bg-white p-4 shadow-[0_8px_24px_rgba(224,64,160,0.08)]">
      <div class="flex items-center justify-between gap-4">
        <div>
          <p class="text-xs font-bold uppercase tracking-[0.2em] text-primary/70">当前行程</p>
          <h2 class="mt-1 text-2xl font-black text-zinc-900">{{ selectedTrip?.title ?? '未选择行程' }}</h2>
        </div>
        <select
          :value="selectedTrip?.id"
          class="rounded-2xl border border-pink-100 bg-rose-50 px-4 py-3 text-sm font-semibold text-zinc-900 focus:border-primary focus:outline-none"
          @change="selectTrip(($event.target as HTMLSelectElement).value)"
        >
          <option v-for="trip in tripList" :key="trip.id" :value="trip.id">
            {{ trip.title }}
          </option>
        </select>
      </div>
    </section>

    <section class="overflow-hidden rounded-3xl bg-white p-4 shadow-[0_8px_24px_rgba(224,64,160,0.1)] sm:p-6">
      <Calendar
        :key="calendarKey"
        class="travel-calendar"
        color="pink"
        locale="zh-CN"
        title-position="left"
        :first-day-of-week="1"
        :initial-page="{ month: selectedDate.getMonth() + 1, year: selectedDate.getFullYear() }"
        :masks="calendarMasks"
        borderless
        transparent
        @dayclick="handleDayClick"
      >
        <template #day-content="{ day, dayProps, dayEvents }">
          <div
            v-bind="dayProps"
            class="calendar-cell"
            :class="{
              'calendar-cell--muted': !day.inMonth,
              'calendar-cell--travel': day.inMonth && isTravelDay(day.date),
              'calendar-cell--travel-start': day.inMonth && isTravelStart(day.date),
              'calendar-cell--selected': day.inMonth && isSelected(day.date) && !isTodayCell(day.date),
              'calendar-cell--today': day.inMonth && isTodayCell(day.date),
            }"
            v-on="dayEvents"
          >
            <span class="calendar-cell__label">{{ day.label }}</span>

            <Sparkles
              v-if="day.inMonth && getMarker(day.date) === 'sparkles'"
              class="calendar-cell__icon calendar-cell__icon--sparkles"
              :size="12"
            />
            <Train
              v-else-if="day.inMonth && getMarker(day.date) === 'train'"
              class="calendar-cell__icon calendar-cell__icon--train"
              :size="12"
            />
            <span
              v-else-if="day.inMonth && getMarker(day.date) === 'dot'"
              class="calendar-cell__dot"
            />
          </div>
        </template>
        <template #footer>
          <div class="calendar-footer">
            <button
              class="bouncy-hover calendar-footer__button"
              type="button"
              @click="jumpToToday"
            >
              Today
            </button>
          </div>
        </template>
      </Calendar>
    </section>

    <section class="grid gap-4 sm:grid-cols-[minmax(0,1.3fr)_minmax(0,0.9fr)]">
      <article class="rounded-3xl bg-white p-5 shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm font-semibold text-outline">{{ selectedDateLabel }}</p>
            <h3 class="mt-1 text-2xl font-black text-zinc-900">{{ selectedPlan.summary }}</h3>
          </div>
          <span class="rounded-full bg-primary-fixed px-3 py-1 text-xs font-black uppercase tracking-wider text-primary">
            {{ selectedPlan.highlight }}
          </span>
        </div>
        <p class="mt-3 text-sm leading-6 text-outline">{{ selectedPlan.hint }}</p>
      </article>

      <article class="rounded-3xl bg-gradient-to-br from-primary-fixed via-white to-secondary-fixed p-5 shadow-[0_8px_20px_rgba(124,82,170,0.12)]">
        <div class="flex items-center gap-3">
          <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-primary shadow-sm">
            <CalendarDays :size="22" />
          </div>
          <div>
            <p class="text-xs font-bold uppercase tracking-[0.2em] text-primary/70">Status</p>
            <p class="text-lg font-black text-zinc-900">{{ selectedPlan.activities.length }} 个活动</p>
          </div>
        </div>
        <div class="mt-4 space-y-3 text-sm text-outline">
          <div class="flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3">
            <span>跨城交通</span>
            <span class="font-bold text-secondary">{{ tripRangeText }}</span>
          </div>
          <div class="flex items-center justify-between rounded-2xl bg-white/80 px-4 py-3">
            <span>选中日期</span>
            <span class="font-bold text-primary">{{ selectedKey }}</span>
          </div>
        </div>
      </article>
    </section>

    <section class="rounded-3xl bg-white p-5 shadow-[0_8px_24px_rgba(0,0,0,0.05)]">
      <div class="flex items-center justify-between gap-3">
        <div>
          <h3 class="text-lg font-bold text-zinc-900">当日摘要</h3>
          <p class="text-sm text-outline">日历页直接维护 TripDay 的 summary / hint / highlight。</p>
        </div>
        <div class="flex gap-2">
          <button class="rounded-full bg-primary px-4 py-2 text-sm font-bold text-white" type="button" @click="saveDayPlan">
            保存当天
          </button>
          <button
            class="rounded-full bg-rose-50 px-4 py-2 text-sm font-bold text-rose-600"
            type="button"
            :disabled="!selectedDayRecord"
            @click="deleteDayPlan"
          >
            清空当天
          </button>
        </div>
      </div>

      <div class="mt-4 grid gap-4 sm:grid-cols-2">
        <label class="space-y-2">
          <span class="text-xs font-bold uppercase tracking-[0.18em] text-outline">摘要</span>
          <input v-model="dayDraft.summary" class="w-full rounded-2xl border border-pink-100 bg-rose-50 px-4 py-3 font-semibold text-zinc-900 focus:border-primary focus:outline-none" type="text">
        </label>
        <label class="space-y-2">
          <span class="text-xs font-bold uppercase tracking-[0.18em] text-outline">标签</span>
          <input v-model="dayDraft.highlightTag" class="w-full rounded-2xl border border-pink-100 bg-rose-50 px-4 py-3 font-semibold text-zinc-900 focus:border-primary focus:outline-none" type="text">
        </label>
        <label class="space-y-2 sm:col-span-2">
          <span class="text-xs font-bold uppercase tracking-[0.18em] text-outline">提示文案</span>
          <textarea v-model="dayDraft.hint" class="min-h-[96px] w-full rounded-2xl border border-pink-100 bg-rose-50 px-4 py-3 text-sm text-zinc-900 focus:border-primary focus:outline-none" />
        </label>
      </div>
    </section>

    <section class="space-y-4">
      <div class="flex items-end justify-between">
        <div>
          <h3 class="text-lg font-bold text-zinc-900">当日安排</h3>
          <p class="text-sm text-outline">点选日历中的任意日期，下面的内容会同步切换。</p>
        </div>
        <button class="bouncy-hover rounded-full bg-secondary px-4 py-2 text-sm font-bold text-white shadow-[0_4px_12px_rgba(124,82,170,0.3)]" type="button" @click="openNewEvent">
          添加活动
        </button>
      </div>

      <article v-if="showEventEditor" class="rounded-3xl border border-pink-100 bg-rose-50/60 p-5 shadow-[0_8px_24px_rgba(224,64,160,0.08)]">
        <div class="flex items-center justify-between gap-3">
          <div>
            <h4 class="text-lg font-bold text-zinc-900">{{ editingEventId ? '编辑活动' : '新增活动' }}</h4>
            <p class="text-sm text-outline">当前会直接写入本地持久化 store。</p>
          </div>
          <button class="rounded-full bg-white px-4 py-2 text-sm font-bold text-zinc-700" type="button" @click="resetEventDraft">
            取消
          </button>
        </div>

        <div class="mt-4 grid gap-4 sm:grid-cols-2">
          <label class="space-y-2 sm:col-span-2">
            <span class="text-xs font-bold uppercase tracking-[0.18em] text-outline">标题</span>
            <input v-model="eventDraft.title" class="w-full rounded-2xl border border-pink-100 bg-white px-4 py-3 font-semibold text-zinc-900 focus:border-primary focus:outline-none" type="text">
          </label>
          <label class="space-y-2">
            <span class="text-xs font-bold uppercase tracking-[0.18em] text-outline">类型</span>
            <select v-model="eventDraft.eventType" class="w-full rounded-2xl border border-pink-100 bg-white px-4 py-3 font-semibold text-zinc-900 focus:border-primary focus:outline-none">
              <option value="activity">活动</option>
              <option value="transport">交通</option>
              <option value="stay">住宿</option>
              <option value="reminder">提醒</option>
            </select>
          </label>
          <label class="space-y-2">
            <span class="text-xs font-bold uppercase tracking-[0.18em] text-outline">时间</span>
            <input v-model="eventDraft.time" class="w-full rounded-2xl border border-pink-100 bg-white px-4 py-3 font-semibold text-zinc-900 focus:border-primary focus:outline-none" type="time">
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-xs font-bold uppercase tracking-[0.18em] text-outline">
              {{ eventDraft.eventType === 'transport' ? '班次 / 票据' : '地点 / 备注' }}
            </span>
            <input v-model="eventDraft.metaValue" class="w-full rounded-2xl border border-pink-100 bg-white px-4 py-3 font-semibold text-zinc-900 focus:border-primary focus:outline-none" type="text">
          </label>
          <label class="space-y-2 sm:col-span-2">
            <span class="text-xs font-bold uppercase tracking-[0.18em] text-outline">说明</span>
            <textarea v-model="eventDraft.description" class="min-h-[96px] w-full rounded-2xl border border-pink-100 bg-white px-4 py-3 text-sm text-zinc-900 focus:border-primary focus:outline-none" />
          </label>
        </div>

        <div class="mt-4 flex items-center justify-end gap-3">
          <button class="rounded-full bg-primary px-5 py-3 text-sm font-bold text-white" type="button" @click="saveEvent">
            {{ editingEventId ? '保存修改' : '创建活动' }}
          </button>
        </div>
      </article>

      <div v-if="selectedPlan.activities.length" class="grid grid-cols-1 gap-4">
        <article
          v-for="(activity, index) in selectedPlan.activities"
          :key="activity.id"
          class="group flex cursor-pointer gap-4 rounded-2xl bg-white p-5 shadow-[0_8px_24px_rgba(0,0,0,0.05)] transition-all hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)]"
          :class="getEventTone(activity) === 'tertiary' ? 'border-l-8 border-tertiary' : 'border-l-8 border-secondary'"
          :style="{ transitionDelay: `${index * 80}ms` }"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-full" :class="getEventTone(activity) === 'tertiary' ? 'bg-tertiary-fixed text-tertiary' : 'bg-secondary-fixed text-secondary'">
            <Utensils v-if="getEventCardIcon(activity) === 'utensils'" :size="24" />
            <Landmark v-else :size="24" />
          </div>
          <div class="flex-1">
            <div class="flex justify-between gap-3">
              <div>
                <h4 class="font-bold text-zinc-900">{{ activity.title }}</h4>
                <p class="mt-1 text-xs text-outline">{{ activity.eventType }}</p>
              </div>
              <div class="text-right">
                <span class="rounded-full px-2 py-0.5 text-[12px] font-bold" :class="getEventTone(activity) === 'tertiary' ? 'bg-tertiary-fixed text-tertiary' : 'bg-secondary-fixed text-secondary'">
                  {{ formatEventTime(activity.startAt) }}
                </span>
              </div>
            </div>
            <p class="mt-1 text-sm text-outline">{{ activity.description }}</p>
            <div class="mt-2 flex items-center gap-1 text-[12px] text-outline">
              <MapPin v-if="getEventMetaIcon(activity) === 'map-pin'" :size="14" />
              <Ticket v-else :size="14" />
              <span>{{ getEventMetaLabel(activity) }}</span>
            </div>
            <div class="mt-4 flex items-center gap-2">
              <button class="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-bold text-zinc-700" type="button" @click="openEditEvent(activity)">
                <FilePenLine :size="14" class="mr-1 inline-block" />
                编辑
              </button>
              <button class="rounded-full bg-rose-50 px-3 py-1.5 text-xs font-bold text-rose-600" type="button" @click="deleteEvent(activity.id)">
                <Trash2 :size="14" class="mr-1 inline-block" />
                删除
              </button>
            </div>
          </div>
        </article>
      </div>

      <article v-else class="rounded-2xl border border-dashed border-pink-200 bg-white/70 p-8 text-center shadow-[0_4px_16px_rgba(0,0,0,0.03)]">
        <div class="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-fixed text-primary">
          <CalendarDays :size="26" />
        </div>
        <h4 class="mt-4 text-lg font-bold text-zinc-900">这一天还没有具体安排</h4>
        <p class="mt-2 text-sm text-outline">你可以继续切换月份并选择日期，或者直接为当前日期创建第一个活动。</p>
        <button class="mt-4 rounded-full bg-secondary px-4 py-2 text-sm font-bold text-white" type="button" @click="openNewEvent">
          新增第一个活动
        </button>
      </article>
    </section>

    <article class="group flex cursor-pointer items-center justify-between rounded-2xl bg-gradient-to-r from-primary-fixed to-secondary-fixed p-6 shadow-sm transition-all hover:shadow-md">
      <div class="flex items-center gap-4">
        <div class="flex h-14 w-14 items-center justify-center rounded-full bg-white text-secondary shadow-sm">
          <Clock3 :size="24" />
        </div>
        <div>
          <p class="text-[12px] font-bold uppercase tracking-tighter text-primary">行程提醒</p>
          <h4 class="font-bold text-zinc-800">{{ selectedPlan.hint }}</h4>
        </div>
      </div>
      <ChevronRight :size="20" class="text-zinc-800 transition-transform group-hover:translate-x-1" />
    </article>

    <button class="group bouncy-hover fixed bottom-24 right-6 z-40 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-white shadow-[0_8px_24px_rgba(224,64,160,0.4)]" type="button" aria-label="新增活动" @click="openNewEvent">
      <Plus :size="32" class="transition-transform duration-300 group-hover:rotate-90" />
    </button>
  </div>
</template>

<style scoped>
:deep(.travel-calendar .vc-container) {
  width: 100%;
  border: 0;
  border-radius: 1.5rem;
  background: linear-gradient(180deg, rgba(255, 250, 253, 0.96), rgba(255, 255, 255, 1));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
  font-family: "DM Sans", ui-sans-serif, system-ui, sans-serif;
}

:deep(.travel-calendar .vc-header) {
  padding: 0.5rem 0.25rem 1rem;
}

:deep(.travel-calendar .vc-title) {
  color: #e040a0;
  font-size: 1.9rem;
  font-weight: 800;
}

:deep(.travel-calendar .vc-arrow) {
  border-radius: 9999px;
  color: #e040a0;
  background: rgba(255, 214, 238, 0.95);
}

:deep(.travel-calendar .vc-arrow:hover) {
  background: rgba(248, 185, 224, 1);
}

:deep(.travel-calendar .vc-weeks) {
  gap: 0.3rem 0;
}

:deep(.travel-calendar .vc-weekday) {
  color: #907898;
  font-size: 0.8rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}

:deep(.travel-calendar .vc-day) {
  min-height: 3.25rem;
}

.calendar-cell {
  position: relative;
  display: flex;
  height: 2.75rem;
  width: 2.75rem;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  font-weight: 800;
  color: #2a2230;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease;
}

.calendar-cell:hover {
  transform: translateY(-1px);
}

.calendar-cell--muted {
  color: #d9cce0;
}

.calendar-cell--travel {
  background: #88d0f0;
  color: #173346;
}

.calendar-cell--travel-start {
  background: #139fd8;
  color: #ffffff;
  box-shadow: 0 10px 22px rgba(19, 159, 216, 0.35);
}

.calendar-cell--selected {
  box-shadow: inset 0 0 0 2px rgba(224, 64, 160, 0.45);
  color: #e040a0;
}

.calendar-cell--today {
  background: #e040a0;
  color: #ffffff;
  box-shadow: 0 10px 22px rgba(224, 64, 160, 0.34);
}

.calendar-cell--today .calendar-cell__label {
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.08);
}

.calendar-cell__label {
  position: relative;
  z-index: 1;
}

.calendar-cell__icon {
  position: absolute;
  right: -0.05rem;
  top: -0.1rem;
  z-index: 2;
}

.calendar-cell__icon--sparkles {
  color: #00a9e8;
}

.calendar-cell__icon--train {
  padding: 0.12rem;
  border-radius: 9999px;
  background: #8d62bd;
  color: #ffffff;
  box-shadow: 0 4px 10px rgba(141, 98, 189, 0.35);
}

.calendar-cell__dot {
  position: absolute;
  bottom: 0.08rem;
  height: 0.38rem;
  width: 0.38rem;
  border-radius: 9999px;
  background: #8d62bd;
}

.calendar-footer {
  display: flex;
  justify-content: center;
  padding: 0.9rem 0 0.15rem;
}

.calendar-footer__button {
  border-radius: 9999px;
  background: rgba(255, 214, 238, 0.95);
  padding: 0.6rem 1.1rem;
  font-size: 0.85rem;
  font-weight: 800;
  color: #e040a0;
  box-shadow: 0 8px 18px rgba(224, 64, 160, 0.12);
}
</style>
