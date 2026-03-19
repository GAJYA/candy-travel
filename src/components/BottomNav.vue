<script setup lang="ts">
import {Calendar, Home, Sparkles, User} from 'lucide-vue-next';
import type {TabId} from '@/types';

defineProps<{
  activeTab: TabId;
}>();

const emit = defineEmits<{
  (event: 'update:activeTab', value: TabId): void;
}>();

const tabs: Array<{id: TabId; label: string; icon: unknown}> = [
  {id: 'home', label: '首页', icon: Home},
  {id: 'calendar', label: '日历', icon: Calendar},
  {id: 'ai', label: 'AI 助手', icon: Sparkles},
  {id: 'profile', label: '我的', icon: User},
];
</script>

<template>
  <nav class="fixed bottom-0 left-0 z-50 flex h-20 w-full items-center justify-around rounded-t-[32px] border-t border-pink-100 bg-white/90 px-4 pb-safe shadow-[0_-8px_24px_rgba(224,64,160,0.1)] backdrop-blur-lg">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      type="button"
      class="relative flex flex-col items-center justify-center px-4 py-2 transition-all duration-300"
      :class="activeTab === tab.id ? 'scale-110 rounded-full bg-primary-fixed px-5 text-primary' : 'text-slate-400 hover:text-primary'"
      @click="emit('update:activeTab', tab.id)"
    >
      <div v-if="activeTab === tab.id" class="absolute inset-0 -z-10 rounded-full bg-primary/10" />
      <component :is="tab.icon" :size="activeTab === tab.id ? 24 : 20" :stroke-width="activeTab === tab.id ? 2.5 : 2" />
      <span class="mt-0.5 font-sans text-[11px] font-medium">{{ tab.label }}</span>
    </button>
  </nav>
</template>
