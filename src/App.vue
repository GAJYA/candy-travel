<script setup lang="ts">
import {computed, ref} from 'vue';
import {ArrowLeft, MoreVertical} from 'lucide-vue-next';
import BottomNav from '@/components/BottomNav.vue';
import AIScreen from '@/components/AIScreen.vue';
import CalendarScreen from '@/components/CalendarScreen.vue';
import HomeScreen from '@/components/HomeScreen.vue';
import ProfileScreen from '@/components/ProfileScreen.vue';
import type {TabId} from '@/types';

const activeTab = ref<TabId>('home');

const tabMeta: Record<TabId, {title: string; component: unknown}> = {
  home: {title: 'Candy Travel', component: HomeScreen},
  calendar: {title: '日历', component: CalendarScreen},
  ai: {title: 'AI 助手', component: AIScreen},
  profile: {title: '个人中心', component: ProfileScreen},
};

const currentTitle = computed(() => tabMeta[activeTab.value].title);
const currentComponent = computed(() => tabMeta[activeTab.value].component);
</script>

<template>
  <div class="min-h-screen bg-background text-zinc-900 selection:bg-primary-fixed">
    <header class="fixed top-0 z-50 flex h-16 w-full items-center justify-between bg-rose-50/80 px-6 shadow-[0_4px_16px_rgba(224,64,160,0.15)] backdrop-blur-md">
      <div class="flex items-center gap-4">
        <button class="bouncy-hover text-primary" type="button" aria-label="返回">
          <ArrowLeft :size="24" />
        </button>
        <h1 class="font-sans text-lg font-bold tracking-tight text-primary">
          {{ currentTitle }}
        </h1>
      </div>

      <div class="flex items-center gap-4">
        <span v-if="activeTab === 'home'" class="hidden font-black italic text-primary sm:inline">
          Candy Travel
        </span>
        <button class="bouncy-hover text-primary" type="button" aria-label="更多">
          <MoreVertical :size="24" />
        </button>
      </div>
    </header>

    <main class="mx-auto max-w-2xl px-4 pt-20">
      <Transition name="screen" mode="out-in">
        <component :is="currentComponent" :key="activeTab" />
      </Transition>
    </main>

    <BottomNav :active-tab="activeTab" @update:active-tab="activeTab = $event" />
  </div>
</template>

<style scoped>
.screen-enter-active,
.screen-leave-active {
  transition: opacity 0.22s ease, transform 0.22s ease;
}

.screen-enter-from {
  opacity: 0;
  transform: translateX(10px);
}

.screen-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}
</style>
