<script setup lang="ts">
import {reactive, ref} from 'vue';
import {
  Bed,
  Bus,
  Car,
  Clock3,
  Coffee,
  Edit3,
  ListChecks,
  MapPin,
  Pill,
  Plane,
  Save,
  Timer,
  Train,
} from 'lucide-vue-next';
import type {PackingItem, TransportMode} from '@/types';

const destination = ref('京都樱花之旅');
const departureTime = ref('09:30');
const arrivalTime = ref('14:15');
const hotel = ref('樱花皇宫大酒店');
const note = ref('');
const activeTransport = ref<TransportMode>('flight');

const transportModes: Array<{
  id: TransportMode;
  label: string;
  icon: unknown;
  activeClass: string;
}> = [
  {id: 'flight', label: '飞机', icon: Plane, activeClass: 'border-primary bg-primary-fixed text-primary shadow-[0_4px_12px_rgba(224,64,160,0.15)]'},
  {id: 'train', label: '火车', icon: Train, activeClass: 'border-secondary bg-secondary-fixed text-secondary shadow-[0_4px_12px_rgba(124,82,170,0.15)]'},
  {id: 'bus', label: '巴士', icon: Bus, activeClass: 'border-tertiary bg-tertiary-fixed text-tertiary shadow-[0_4px_12px_rgba(0,150,204,0.15)]'},
  {id: 'car', label: '自驾', icon: Car, activeClass: 'border-primary-container bg-primary-fixed-dim text-primary'},
];

const packingItems = reactive<PackingItem[]>([
  {label: '相机与镜头', checked: true},
  {label: '便携式充电器', checked: false},
  {label: '护照', checked: true},
]);
</script>

<template>
  <div class="space-y-6 pb-24">
    <section class="group relative">
      <div class="absolute -inset-1 rounded-2xl bg-gradient-to-r from-primary to-secondary opacity-10 blur transition duration-1000 group-hover:opacity-20" />
      <div class="relative rounded-2xl bg-white p-6 shadow-[0_8px_32px_rgba(224,64,160,0.08)]">
        <label class="mb-2 block px-1 text-sm font-bold text-primary">下一站去哪？</label>
        <div class="flex items-center gap-3 rounded-full border-2 border-transparent bg-surface-variant/50 px-5 py-3 transition-all focus-within:border-primary">
          <MapPin :size="20" class="text-tertiary" />
          <input
            v-model="destination"
            class="w-full border-none bg-transparent font-bold text-zinc-900 placeholder:text-outline-variant focus:ring-0"
            placeholder="梦想目的地"
            type="text"
          >
        </div>
      </div>
    </section>

    <section class="space-y-3">
      <h2 class="flex items-center gap-2 px-2 text-lg font-bold text-zinc-900">
        <Plane :size="20" class="text-secondary" />
        如何抵达？
      </h2>
      <div class="grid grid-cols-4 gap-3">
        <button
          v-for="mode in transportModes"
          :key="mode.id"
          type="button"
          class="bouncy-hover flex flex-col items-center gap-2 rounded-2xl border-2 p-4 transition-all"
          :class="activeTransport === mode.id ? ['scale-105', mode.activeClass] : 'border-transparent bg-white text-outline shadow-[0_4px_12px_rgba(0,0,0,0.05)]'"
          @click="activeTransport = mode.id"
        >
          <component :is="mode.icon" :size="28" />
          <span class="text-[10px] font-bold uppercase tracking-wider">{{ mode.label }}</span>
        </button>
      </div>
    </section>

    <section class="grid grid-cols-2 gap-4">
      <div class="rounded-2xl bg-white p-4 shadow-[0_4px_12px_rgba(0,0,0,0.05)]">
        <label class="mb-2 block text-[11px] font-bold uppercase tracking-widest text-secondary">出发</label>
        <div class="flex items-center gap-2 text-zinc-900">
          <Clock3 :size="16" class="text-secondary" />
          <input v-model="departureTime" class="w-full border-none bg-transparent p-0 font-bold focus:ring-0" type="time">
        </div>
      </div>
      <div class="rounded-2xl bg-white p-4 shadow-[0_4px_12px_rgba(0,0,0,0.05)]">
        <label class="mb-2 block text-[11px] font-bold uppercase tracking-widest text-tertiary">到达</label>
        <div class="flex items-center gap-2 text-zinc-900">
          <Timer :size="16" class="text-tertiary" />
          <input v-model="arrivalTime" class="w-full border-none bg-transparent p-0 font-bold focus:ring-0" type="time">
        </div>
      </div>
    </section>

    <section class="rounded-2xl bg-secondary-container p-6 shadow-[0_8px_24px_rgba(124,82,170,0.1)]">
      <h2 class="mb-4 flex items-center gap-2 text-sm font-bold text-secondary">
        <Bed :size="18" />
        入住酒店
      </h2>
      <div class="rounded-2xl border border-white bg-white/60 p-4 backdrop-blur-sm">
        <input
          v-model="hotel"
          class="w-full border-none bg-transparent font-medium text-zinc-800 placeholder:text-secondary-fixed-dim focus:ring-0"
          placeholder="酒店名称或地址..."
          type="text"
        >
      </div>
    </section>

    <section class="space-y-3">
      <h2 class="flex items-center gap-2 px-2 text-lg font-bold text-zinc-900">
        <ListChecks :size="20" class="text-primary" />
        准备好了吗？
      </h2>
      <div class="grid grid-cols-12 gap-3">
        <div class="col-span-7 rounded-2xl bg-white p-4 shadow-[0_4px_16px_rgba(0,0,0,0.04)]">
          <div class="space-y-3">
            <label v-for="item in packingItems" :key="item.label" class="group flex cursor-pointer items-center gap-3">
              <input v-model="item.checked" class="h-5 w-5 rounded-full text-primary transition-all focus:ring-primary" type="checkbox">
              <span class="text-sm font-medium text-zinc-800 transition-colors group-hover:text-primary">{{ item.label }}</span>
            </label>
          </div>
        </div>
        <div class="col-span-5 flex flex-col gap-3">
          <div class="bouncy-hover flex flex-1 flex-col items-center justify-center rounded-2xl bg-tertiary-fixed p-4 text-center">
            <Coffee :size="20" class="mb-1 text-tertiary" />
            <span class="text-[10px] font-bold uppercase text-tertiary">零食</span>
          </div>
          <div class="bouncy-hover flex flex-1 flex-col items-center justify-center rounded-2xl bg-primary-fixed p-4 text-center">
            <Pill :size="20" class="mb-1 text-primary" />
            <span class="text-[10px] font-bold uppercase text-primary">药品</span>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-2xl bg-white p-6 shadow-[0_8px_32px_rgba(0,0,0,0.04)]">
      <label class="mb-3 flex items-center gap-2 text-sm font-bold text-outline">
        <Edit3 :size="14" />
        旅行笔记
      </label>
      <textarea
        v-model="note"
        class="w-full resize-none rounded-2xl border-none bg-surface-variant/50 p-4 text-sm font-medium text-zinc-800 focus:ring-2 focus:ring-primary/20"
        placeholder="别忘了带雨伞，预约代码是 #12345..."
        rows="3"
      />
    </section>

    <div class="pb-8 pt-4">
      <button class="bouncy-hover candy-shadow-primary flex w-full items-center justify-center gap-3 rounded-full bg-primary py-5 text-lg font-black text-white" type="button">
        <Save :size="24" />
        保存计划
      </button>
    </div>
  </div>
</template>
