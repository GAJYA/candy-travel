<script setup lang="ts">
import {ChevronRight, Map, Plane, Plus, Sparkles, Train} from 'lucide-vue-next';
import type {UpcomingTrip} from '@/types';

const upcomingTrips: UpcomingTrip[] = [
  {
    city: '日本京都',
    date: '2024年11月4日 - 11月8日',
    status: 'confirmed',
    iconBgClass: 'bg-secondary-fixed group-hover:bg-secondary',
    iconTextClass: 'text-secondary group-hover:text-white',
    statusClass: 'bg-tertiary-fixed text-tertiary',
    kind: 'train',
  },
  {
    city: '韩国首尔',
    date: '2024年12月5日 - 12月9日',
    status: 'planning',
    iconBgClass: 'bg-primary-fixed group-hover:bg-primary',
    iconTextClass: 'text-primary group-hover:text-white',
    statusClass: 'bg-secondary-fixed text-secondary',
    kind: 'plane',
  },
];

const tripStatusLabel = {
  confirmed: '已确认',
  planning: '规划中',
} as const;
</script>

<template>
  <div class="space-y-6 pb-24">
    <section class="group relative overflow-hidden rounded-3xl bg-primary p-6 text-white candy-shadow-primary">
      <div class="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-white/10 blur-2xl" />
      <div class="absolute -bottom-4 -left-4 h-24 w-24 rounded-full bg-secondary/20 blur-xl" />

      <div class="relative z-10 flex flex-col items-center">
        <span class="mb-2 text-xs font-bold uppercase tracking-widest opacity-80">下一次冒险开始于</span>
        <div class="flex items-center gap-4">
          <div class="flex flex-col items-center">
            <span class="text-4xl font-black">12</span>
            <span class="text-[10px] font-medium opacity-90">天</span>
          </div>
          <span class="text-2xl font-light opacity-40">:</span>
          <div class="flex flex-col items-center">
            <span class="text-4xl font-black">08</span>
            <span class="text-[10px] font-medium opacity-90">时</span>
          </div>
          <span class="text-2xl font-light opacity-40">:</span>
          <div class="flex flex-col items-center">
            <span class="text-4xl font-black">45</span>
            <span class="text-[10px] font-medium opacity-90">分</span>
          </div>
        </div>
        <button class="bouncy-hover mt-4 flex items-center gap-2 rounded-full bg-white/20 px-6 py-2 backdrop-blur-sm transition-all hover:bg-white/30" type="button">
          <Plane :size="14" />
          <span class="text-sm font-bold">前往 日本东京</span>
        </button>
      </div>
    </section>

    <section class="grid grid-cols-2 gap-4">
      <div class="col-span-2 flex items-center justify-between rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_4px_16px_rgba(124,82,170,0.1)]">
        <div>
          <p class="text-sm font-medium text-outline">2024 年度旅程</p>
          <p class="text-2xl font-black text-secondary">缤纷世界</p>
        </div>
        <div class="flex h-12 w-12 items-center justify-center rounded-full bg-secondary-container text-secondary">
          <Sparkles :size="24" />
        </div>
      </div>

      <div class="bouncy-hover flex flex-col items-center rounded-2xl border border-pink-100 bg-primary-fixed/30 p-4 text-center">
        <span class="text-3xl font-black text-primary">14</span>
        <span class="mt-1 text-xs font-bold uppercase text-outline">计划城市</span>
      </div>

      <div class="bouncy-hover flex flex-col items-center rounded-2xl border border-pink-100 bg-tertiary-fixed/30 p-4 text-center">
        <span class="text-3xl font-black text-tertiary">08</span>
        <span class="mt-1 text-xs font-bold uppercase text-outline">旅行次数</span>
      </div>

      <div class="relative col-span-2 flex items-center justify-between overflow-hidden rounded-2xl bg-tertiary p-5 text-white candy-shadow-tertiary">
        <div class="absolute -bottom-4 -right-4 opacity-10">
          <Map :size="96" />
        </div>
        <div>
          <p class="text-xs font-bold uppercase tracking-tighter opacity-80">行程距离</p>
          <p class="text-3xl font-black">24,530 <span class="text-sm font-medium">km</span></p>
        </div>
        <div class="flex -space-x-2">
          <div class="flex h-8 w-8 items-center justify-center rounded-full border border-white/30 bg-white/20 backdrop-blur-md">
            <Plane :size="16" />
          </div>
          <div class="flex h-8 w-8 items-center justify-center rounded-full border border-white/30 bg-white/20 backdrop-blur-md">
            <Train :size="16" />
          </div>
        </div>
      </div>
    </section>

    <section class="overflow-hidden rounded-2xl border border-pink-50 bg-white shadow-[0_4px_16px_rgba(224,64,160,0.1)]">
      <div class="flex items-center justify-between border-b border-pink-50 p-4">
        <h2 class="flex items-center gap-2 font-bold text-secondary">
          <Map :size="18" class="text-primary" />
          我的足迹
        </h2>
        <span class="rounded-full bg-primary-fixed px-3 py-1 text-[10px] font-black uppercase text-primary">全球视图</span>
      </div>
      <div class="relative flex h-48 w-full items-center justify-center overflow-hidden bg-slate-50">
        <img
          src="https://picsum.photos/seed/travel-map/600/300"
          alt="Map"
          class="h-full w-full object-cover opacity-40"
          referrerpolicy="no-referrer"
        >
        <div class="absolute inset-0 flex items-center justify-center">
          <div class="relative h-full w-full">
            <svg class="absolute inset-0 h-full w-full" viewBox="0 0 400 200">
              <path d="M50,100 Q200,20 350,100" fill="none" stroke="#e040a0" stroke-dasharray="4,4" stroke-width="2" />
              <circle cx="50" cy="100" fill="#e040a0" r="4" />
              <circle cx="350" cy="100" fill="#e040a0" r="4" />
            </svg>
          </div>
        </div>
        <div class="absolute bottom-4 left-4 flex items-center gap-3 rounded-xl border border-white/50 bg-white/70 px-3 py-2 shadow-sm backdrop-blur-md">
          <div class="flex items-center gap-1">
            <span class="h-2 w-2 rounded-full bg-primary" />
            <span class="text-[10px] font-bold">当前</span>
          </div>
          <div class="flex items-center gap-1">
            <span class="h-2 w-2 rounded-full bg-secondary" />
            <span class="text-[10px] font-bold">已计划</span>
          </div>
        </div>
      </div>
    </section>

    <section class="space-y-4">
      <h2 class="px-2 text-lg font-black text-zinc-900">即将到来的行程</h2>
      <div class="space-y-3">
        <article
          v-for="trip in upcomingTrips"
          :key="trip.city"
          class="group flex cursor-pointer items-center gap-4 rounded-2xl border border-pink-50 bg-white p-4 shadow-[0_4px_16px_rgba(0,0,0,0.05)] transition-all hover:scale-[1.01] active:scale-[0.98]"
        >
          <div class="flex h-14 w-14 items-center justify-center rounded-xl transition-colors duration-300" :class="[trip.iconBgClass, trip.iconTextClass]">
            <Plane v-if="trip.kind === 'plane'" :size="24" />
            <Train v-else :size="24" />
          </div>
          <div class="flex-1">
            <h3 class="font-bold text-zinc-900">{{ trip.city }}</h3>
            <p class="text-xs text-outline">{{ trip.date }}</p>
          </div>
          <div class="text-right">
            <span class="mb-1 block rounded-full px-2 py-0.5 text-[10px] font-black" :class="trip.statusClass">
              {{ tripStatusLabel[trip.status] }}
            </span>
            <ChevronRight :size="16" class="ml-auto text-pink-200 transition-colors group-hover:text-primary" />
          </div>
        </article>
      </div>
    </section>

    <button class="bouncy-hover fixed bottom-24 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-white shadow-[0_8px_24px_rgba(224,64,160,0.4)]" type="button" aria-label="添加行程">
      <Plus :size="30" />
    </button>
  </div>
</template>
