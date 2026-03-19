<script setup lang="ts">
import {
  ChevronLeft,
  ChevronRight,
  Landmark,
  MapPin,
  Plane,
  Plus,
  Ticket,
  Train,
  Utensils,
} from 'lucide-vue-next';
import type {CalendarActivity} from '@/types';

const days = ['日', '一', '二', '三', '四', '五', '六'];
const dates = Array.from({length: 31}, (_, index) => index + 1);

const activities: CalendarActivity[] = [
  {
    title: '在横滨吃午餐',
    time: '12:30 PM',
    description: '寿司与拉面双拼的轻松午后',
    meta: '东京湾区',
    tone: 'tertiary',
    icon: 'utensils',
    metaIcon: 'map-pin',
  },
  {
    title: '数字艺术馆',
    time: '3:00 PM',
    description: '沉浸式体验 teamLab 无界展',
    meta: '门票已确认',
    tone: 'secondary',
    icon: 'landmark',
    metaIcon: 'ticket',
  },
];

const getDayState = (date: number) => ({
  isTripStart: date === 4,
  isTripDay: date >= 5 && date <= 7,
  isSelected: date === 13,
  hasEvent: date === 16,
});
</script>

<template>
  <div class="space-y-6 pb-24">
    <section class="rounded-3xl bg-white p-6 shadow-[0_8px_24px_rgba(224,64,160,0.1)]">
      <div class="mb-6 flex items-center justify-between">
        <h2 class="text-xl font-bold text-primary">2024年10月</h2>
        <div class="flex gap-2">
          <button class="bouncy-hover flex h-10 w-10 items-center justify-center rounded-full bg-primary-fixed transition-colors hover:bg-primary-container" type="button">
            <ChevronLeft :size="20" class="text-primary" />
          </button>
          <button class="bouncy-hover flex h-10 w-10 items-center justify-center rounded-full bg-primary-fixed transition-colors hover:bg-primary-container" type="button">
            <ChevronRight :size="20" class="text-primary" />
          </button>
        </div>
      </div>

      <div class="mb-2 grid grid-cols-7 text-center">
        <span v-for="day in days" :key="day" class="text-[12px] font-bold uppercase tracking-widest text-outline">
          {{ day }}
        </span>
      </div>

      <div class="grid grid-cols-7 gap-y-2">
        <div class="flex h-12 items-center justify-center text-outline-variant">29</div>
        <div class="flex h-12 items-center justify-center text-outline-variant">30</div>

        <div v-for="date in dates" :key="date" class="group relative flex h-12 cursor-pointer items-center justify-center">
          <template v-if="getDayState(date).isTripStart">
            <div class="absolute inset-1 flex items-center justify-center rounded-full bg-tertiary shadow-[0_4px_12px_rgba(0,150,204,0.3)]">
              <span class="font-bold text-white">{{ date }}</span>
              <Plane :size="10" class="absolute -right-1 -top-1 rounded-full bg-white p-0.5 text-tertiary shadow-sm" />
            </div>
          </template>

          <template v-else-if="getDayState(date).isTripDay">
            <div class="absolute inset-1 flex items-center justify-center rounded-full bg-tertiary-fixed-dim">
              <span class="font-bold text-zinc-800">{{ date }}</span>
              <Train v-if="date === 7" :size="10" class="absolute -right-1 -top-1 rounded-full bg-white p-0.5 text-secondary shadow-sm" />
            </div>
          </template>

          <template v-else-if="getDayState(date).isSelected">
            <div class="candy-shadow-primary absolute inset-1 z-10 flex scale-110 items-center justify-center rounded-full border-4 border-primary-fixed bg-primary">
              <span class="font-bold text-white">{{ date }}</span>
            </div>
          </template>

          <template v-else>
            <span class="z-10 font-bold text-zinc-800">{{ date }}</span>
            <div class="absolute inset-0 scale-0 rounded-full bg-secondary-fixed transition-transform group-hover:scale-90" />
            <div v-if="getDayState(date).hasEvent" class="absolute bottom-1 h-1.5 w-1.5 rounded-full bg-secondary" />
          </template>
        </div>
      </div>
    </section>

    <section class="space-y-4">
      <div class="mb-2 flex items-end justify-between">
        <div>
          <h3 class="text-lg font-bold text-zinc-900">10月13日 星期日</h3>
          <p class="text-sm text-outline">您已计划 2 项活动</p>
        </div>
        <button class="bouncy-hover rounded-full bg-secondary px-4 py-2 text-sm font-bold text-white shadow-[0_4px_12px_rgba(124,82,170,0.3)]" type="button">
          添加活动
        </button>
      </div>

      <div class="grid grid-cols-1 gap-4">
        <article
          v-for="(activity, index) in activities"
          :key="activity.title"
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

        <article class="group flex cursor-pointer items-center justify-between rounded-2xl bg-gradient-to-r from-primary-fixed to-secondary-fixed p-6 shadow-sm transition-all hover:shadow-md">
          <div class="flex items-center gap-4">
            <div class="h-14 w-14 overflow-hidden rounded-full border-2 border-white shadow-sm">
              <img
                class="h-full w-full object-cover"
                src="https://picsum.photos/seed/kyoto/100/100"
                alt="Kyoto"
                referrerpolicy="no-referrer"
              >
            </div>
            <div>
              <p class="text-[12px] font-bold uppercase tracking-tighter text-primary">明日预告</p>
              <h4 class="font-bold text-zinc-800">前往京都的新干线</h4>
            </div>
          </div>
          <ChevronRight :size="20" class="text-zinc-800 transition-transform group-hover:translate-x-1" />
        </article>
      </div>
    </section>

    <button class="group bouncy-hover fixed bottom-24 right-6 z-40 flex h-16 w-16 items-center justify-center rounded-full bg-primary text-white shadow-[0_8px_24px_rgba(224,64,160,0.4)]" type="button" aria-label="新增活动">
      <Plus :size="32" class="transition-transform duration-300 group-hover:rotate-90" />
    </button>
  </div>
</template>
