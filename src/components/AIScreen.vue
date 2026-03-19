<script setup lang="ts">
import {ref} from 'vue';
import {
  Calendar as CalendarIcon,
  Clock,
  Edit3,
  Image as ImageIcon,
  ListChecks,
  Plane,
  Save,
  Sparkles,
  Trash2,
} from 'lucide-vue-next';

const inputText = ref('');
const isExtracting = ref(false);
const showResults = ref(false);

const packingItems = ['电子身份证', '电子票据', '充电宝', '防晒霜'];

const handleExtract = () => {
  isExtracting.value = true;
  window.setTimeout(() => {
    isExtracting.value = false;
    showResults.value = true;
  }, 1500);
};
</script>

<template>
  <div class="space-y-8 pb-24">
    <section class="space-y-2">
      <div class="flex items-center gap-3">
        <div class="flex h-12 w-12 items-center justify-center rounded-full bg-primary-container shadow-[0_4px_12px_rgba(224,64,160,0.2)]">
          <Sparkles :size="24" class="text-white" />
        </div>
        <div>
          <h2 class="text-2xl font-bold text-primary">魔法助手</h2>
          <p class="text-sm text-outline">粘贴行程信息或上传票据图片，一键提取旅行安排。</p>
        </div>
      </div>
    </section>

    <section class="space-y-4">
      <div class="group relative">
        <textarea
          v-model="inputText"
          class="min-h-[160px] w-full resize-none rounded-2xl border-2 border-pink-100 bg-white p-6 text-zinc-800 shadow-[0_8px_24px_rgba(0,0,0,0.04)] transition-all duration-300 focus:border-primary focus:ring-4 focus:ring-primary/10"
          placeholder="在此粘贴航班、酒店或活动信息..."
        />
        <div class="absolute bottom-4 right-4 flex gap-2">
          <button class="bouncy-hover flex items-center gap-2 rounded-full bg-secondary-fixed px-4 py-2 text-sm font-bold text-secondary shadow-[0_4px_12px_rgba(124,82,170,0.2)]" type="button">
            <ImageIcon :size="16" />
            上传票据图片
          </button>
        </div>
      </div>

      <button
        class="flex w-full items-center justify-center gap-3 rounded-full bg-primary py-4 text-lg font-bold text-white shadow-[0_8px_24px_rgba(224,64,160,0.3)] transition-all duration-300 hover:scale-[1.02] active:scale-95 disabled:opacity-70"
        type="button"
        :disabled="isExtracting"
        @click="handleExtract"
      >
        <Sparkles v-if="!isExtracting" :size="24" />
        <Sparkles v-else :size="24" class="animate-spin" />
        {{ isExtracting ? '正在提取中...' : '开始智能提取' }}
      </button>
    </section>

    <Transition name="fade-up">
      <section v-if="showResults" class="space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="px-2 text-lg font-bold text-zinc-900">提取详情</h3>
          <span class="rounded-full bg-tertiary-fixed px-3 py-1 text-xs font-bold uppercase tracking-wider text-tertiary">待确认</span>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div class="bouncy-hover rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_8px_20px_rgba(224,64,160,0.08)]">
            <div class="mb-3 flex items-center gap-2 text-primary">
              <CalendarIcon :size="20" />
              <span class="text-xs font-bold uppercase tracking-tight">日期</span>
            </div>
            <p class="text-lg font-bold text-zinc-900">2024年10月19日</p>
            <p class="mt-1 text-xs text-outline">星期六</p>
          </div>

          <div class="bouncy-hover rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_8px_20px_rgba(224,64,160,0.08)]">
            <div class="mb-3 flex items-center gap-2 text-tertiary">
              <Clock :size="20" />
              <span class="text-xs font-bold uppercase tracking-tight">时间</span>
            </div>
            <p class="text-lg font-bold text-zinc-900">10:00 AM</p>
            <p class="mt-1 text-xs text-outline">预计到达：12:30 PM</p>
          </div>

          <div class="bouncy-hover col-span-2 flex items-center justify-between rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_8px_20px_rgba(224,64,160,0.08)]">
            <div class="flex items-center gap-4">
              <div class="flex h-12 w-12 items-center justify-center rounded-full bg-secondary-container text-secondary">
                <Plane :size="24" />
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="text-xs font-bold uppercase tracking-tight text-secondary">交通</span>
                  <span class="rounded-full bg-secondary/10 px-2 py-0.5 text-[10px] font-black text-secondary">MU5101</span>
                </div>
                <p class="text-lg font-bold text-zinc-900">北京 → 上海</p>
              </div>
            </div>
            <Edit3 :size="20" class="text-outline" />
          </div>

          <div class="col-span-2 rounded-2xl border-2 border-dashed border-secondary/20 bg-secondary-fixed/30 p-5">
            <div class="mb-4 flex items-center gap-2 text-secondary">
              <ListChecks :size="20" />
              <span class="text-xs font-bold uppercase tracking-tight">准备清单</span>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <label v-for="(item, index) in packingItems" :key="item" class="group flex cursor-pointer items-center gap-3 rounded-full bg-white/60 p-2">
                <input class="h-5 w-5 rounded-full border-secondary text-secondary focus:ring-secondary/20" type="checkbox" :checked="index < 2">
                <span class="text-sm font-medium text-zinc-800">{{ item }}</span>
              </label>
            </div>
          </div>
        </div>

        <div class="flex gap-4 pt-4">
          <button class="flex flex-1 items-center justify-center gap-2 rounded-full bg-surface-variant py-4 font-bold text-zinc-800 transition-colors hover:bg-outline-variant" type="button">
            <Trash2 :size="20" />
            放弃
          </button>
          <button class="bouncy-hover candy-shadow-tertiary flex flex-[2] items-center justify-center gap-2 rounded-full bg-tertiary py-4 font-bold text-white" type="button">
            <Save :size="20" />
            确认并保存
          </button>
        </div>
      </section>
    </Transition>
  </div>
</template>

<style scoped>
.fade-up-enter-active,
.fade-up-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.fade-up-enter-from,
.fade-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
