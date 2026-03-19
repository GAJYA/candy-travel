<script setup lang="ts">
import {computed, ref} from 'vue';
import {Calendar} from 'v-calendar';
import {
  CalendarDays,
  ChevronRight,
  Landmark,
  MapPin,
  Plane,
  Plus,
  Sparkles,
  Ticket,
  Train,
  Utensils,
} from 'lucide-vue-next';

interface ActivityCard {
  title: string;
  time: string;
  description: string;
  meta: string;
  tone: 'tertiary' | 'secondary';
  icon: 'utensils' | 'landmark';
  metaIcon: 'map-pin' | 'ticket';
}

interface DayPlan {
  summary: string;
  hint: string;
  highlight: string;
  activities: ActivityCard[];
}

type MarkerKind = 'sparkles' | 'train' | 'dot';
type ClickedDay = {
  date: Date;
};

const today = new Date();
const currentYear = today.getFullYear();
const currentMonth = today.getMonth();
const selectedDate = ref(new Date(currentYear, currentMonth, today.getDate()));
const calendarKey = ref(0);

const createDate = (day: number) => new Date(currentYear, currentMonth, day);
const formatKey = (date: Date) => {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');

  return `${year}-${month}-${day}`;
};

const dates = {
  tripStart: createDate(4),
  tripDays: [createDate(5), createDate(6), createDate(7)],
  featuredDay: createDate(13),
  dotDay: createDate(16),
};

const plansByDate: Record<string, DayPlan> = {
  [formatKey(dates.tripStart)]: {
    summary: '出发日',
    hint: '今天正式启程，记得提前在线值机并预留足够的机场交通时间。',
    highlight: '出发',
    activities: [
      {
        title: '飞往东京',
        time: '08:40',
        description: '国际航班 MU523，值机和托运都已准备好。',
        meta: '浦东国际机场 T1',
        tone: 'tertiary',
        icon: 'utensils',
        metaIcon: 'map-pin',
      },
    ],
  },
  [formatKey(dates.tripDays[0])]: {
    summary: '城市探索',
    hint: '轻松适应旅程节奏，优先安排步行可达的点位。',
    highlight: '漫游',
    activities: [
      {
        title: '浅草寺晨间散步',
        time: '09:30',
        description: '拍照、抽签并顺路吃一份热腾腾的人形烧。',
        meta: '台东区浅草',
        tone: 'tertiary',
        icon: 'utensils',
        metaIcon: 'map-pin',
      },
      {
        title: 'teamLab Borderless',
        time: '15:00',
        description: '提前 15 分钟到场，门票已预订。',
        meta: '电子门票已确认',
        tone: 'secondary',
        icon: 'landmark',
        metaIcon: 'ticket',
      },
    ],
  },
  [formatKey(dates.tripDays[2])]: {
    summary: '换城日',
    hint: '今天改乘新干线前往京都，站内换乘信息已提前整理好。',
    highlight: '移动',
    activities: [
      {
        title: '东京站出发去京都',
        time: '10:20',
        description: '乘坐东海道新干线 Nozomi，车票已出票。',
        meta: '东京站 18 号站台',
        tone: 'secondary',
        icon: 'landmark',
        metaIcon: 'ticket',
      },
    ],
  },
  [formatKey(dates.featuredDay)]: {
    summary: '精选安排',
    hint: '这是本月安排最丰富的一天，适合把重点活动放在今天。',
    highlight: '重点',
    activities: [
      {
        title: '在横滨吃午餐',
        time: '12:30',
        description: '寿司与拉面双拼的轻松午后。',
        meta: '东京湾区',
        tone: 'tertiary',
        icon: 'utensils',
        metaIcon: 'map-pin',
      },
      {
        title: '数字艺术馆',
        time: '15:00',
        description: '沉浸式体验 teamLab 无界展。',
        meta: '门票已确认',
        tone: 'secondary',
        icon: 'landmark',
        metaIcon: 'ticket',
      },
    ],
  },
  [formatKey(dates.dotDay)]: {
    summary: '轻松日程',
    hint: '今天只有一项轻量事件，适合购物、发呆或在咖啡馆慢慢坐一会儿。',
    highlight: '轻松',
    activities: [
      {
        title: '银座购物补货',
        time: '14:00',
        description: '补齐伴手礼，顺带去附近咖啡馆休息。',
        meta: '中央区银座',
        tone: 'tertiary',
        icon: 'utensils',
        metaIcon: 'map-pin',
      },
    ],
  },
};

const tripRangeText = computed(() => {
  const formatter = new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
  });

  return `${formatter.format(dates.tripStart)} - ${formatter.format(dates.tripDays[2])}`;
});

const selectedKey = computed(() => formatKey(selectedDate.value));

const selectedPlan = computed<DayPlan>(() => {
  return (
    plansByDate[selectedKey.value] ?? {
      summary: '今天还没有安排行程',
      hint: '可以继续切换月份并点选日期，然后直接为这一天创建新的活动。',
      highlight: '空闲',
      activities: [],
    }
  );
});

const selectedDateLabel = computed(() => {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(selectedDate.value);
});

const markerMap: Record<string, MarkerKind> = {
  [formatKey(dates.tripStart)]: 'sparkles',
  [formatKey(dates.tripDays[2])]: 'train',
  [formatKey(dates.dotDay)]: 'dot',
};

const travelDayKeys = new Set([
  formatKey(dates.tripStart),
  ...dates.tripDays.map(formatKey),
]);

const calendarMasks = {
  title: 'YYYY年M月',
  weekdays: 'W',
};

const isSameDate = (left: Date, right: Date) =>
  left.getFullYear() === right.getFullYear() &&
  left.getMonth() === right.getMonth() &&
  left.getDate() === right.getDate();

const getMarker = (date: Date) => markerMap[formatKey(date)] ?? null;
const isSelected = (date: Date) => isSameDate(date, selectedDate.value);
const isTodayCell = (date: Date) => isSameDate(date, today);
const isTravelDay = (date: Date) => travelDayKeys.has(formatKey(date));
const isTravelStart = (date: Date) => isSameDate(date, dates.tripStart);

const jumpToToday = () => {
  selectedDate.value = new Date();
  calendarKey.value += 1;
};

const handleDayClick = (day: ClickedDay) => {
  selectedDate.value = day.date;
};
</script>

<template>
  <div class="space-y-6 pb-24">
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

    <section class="space-y-4">
      <div class="flex items-end justify-between">
        <div>
          <h3 class="text-lg font-bold text-zinc-900">当日安排</h3>
          <p class="text-sm text-outline">点选日历中的任意日期，下面的内容会同步切换。</p>
        </div>
        <button class="bouncy-hover rounded-full bg-secondary px-4 py-2 text-sm font-bold text-white shadow-[0_4px_12px_rgba(124,82,170,0.3)]" type="button">
          添加活动
        </button>
      </div>

      <div v-if="selectedPlan.activities.length" class="grid grid-cols-1 gap-4">
        <article
          v-for="(activity, index) in selectedPlan.activities"
          :key="`${selectedKey}-${activity.title}`"
          class="group flex cursor-pointer gap-4 rounded-2xl bg-white p-5 shadow-[0_8px_24px_rgba(0,0,0,0.05)] transition-all hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)]"
          :class="activity.tone === 'tertiary' ? 'border-l-8 border-tertiary' : 'border-l-8 border-secondary'"
          :style="{ transitionDelay: `${index * 80}ms` }"
        >
          <div class="flex h-12 w-12 items-center justify-center rounded-full" :class="activity.tone === 'tertiary' ? 'bg-tertiary-fixed text-tertiary' : 'bg-secondary-fixed text-secondary'">
            <Utensils v-if="activity.icon === 'utensils'" :size="24" />
            <Landmark v-else :size="24" />
          </div>
          <div class="flex-1">
            <div class="flex justify-between gap-3">
              <h4 class="font-bold text-zinc-900">{{ activity.title }}</h4>
              <span class="rounded-full px-2 py-0.5 text-[12px] font-bold" :class="activity.tone === 'tertiary' ? 'bg-tertiary-fixed text-tertiary' : 'bg-secondary-fixed text-secondary'">
                {{ activity.time }}
              </span>
            </div>
            <p class="mt-1 text-sm text-outline">{{ activity.description }}</p>
            <div class="mt-2 flex items-center gap-1 text-[12px] text-outline">
              <MapPin v-if="activity.metaIcon === 'map-pin'" :size="14" />
              <Ticket v-else :size="14" />
              <span>{{ activity.meta }}</span>
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
      </article>
    </section>

    <article class="group flex cursor-pointer items-center justify-between rounded-2xl bg-gradient-to-r from-primary-fixed to-secondary-fixed p-6 shadow-sm transition-all hover:shadow-md">
      <div class="flex items-center gap-4">
        <div class="flex h-14 w-14 items-center justify-center rounded-full bg-white text-secondary shadow-sm">
          <Train :size="24" />
        </div>
        <div>
          <p class="text-[12px] font-bold uppercase tracking-tighter text-primary">行程提醒</p>
          <h4 class="font-bold text-zinc-800">本月 7 日乘坐新干线前往京都</h4>
        </div>
      </div>
      <ChevronRight :size="20" class="text-zinc-800 transition-transform group-hover:translate-x-1" />
    </article>

    <button class="group bouncy-hover fixed bottom-24 right-6 z-40 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-white shadow-[0_8px_24px_rgba(224,64,160,0.4)]" type="button" aria-label="新增活动">
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
