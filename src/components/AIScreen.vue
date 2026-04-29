<script setup lang="ts">
import {computed, ref} from 'vue';
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  Clock,
  Edit3,
  Image as ImageIcon,
  ListChecks,
  MapPin,
  Plane,
  Save,
  Sparkles,
  Trash2,
  TriangleAlert,
} from 'lucide-vue-next';

type DraftConfidence = 'high' | 'medium' | 'low';

type DraftField = {
  value: string;
  confidence: DraftConfidence;
};

type DraftExtraction = {
  tripTitle: DraftField;
  travelDate: DraftField;
  departureTime: DraftField;
  arrivalTime: DraftField;
  origin: DraftField;
  destination: DraftField;
  reference: DraftField;
  hotel: DraftField;
  packingItems: Array<{
    label: string;
    checked: boolean;
  }>;
  warnings: string[];
};

const sampleInput = `5月18日 北京飞上海，航班 MU5101，09:30 起飞，11:45 落地。
入住南京西路附近的静安嘉里酒店两晚。
记得带身份证、充电宝，周日晚上去外滩。`;

const inputText = ref(sampleInput);
const isExtracting = ref(false);
const draft = ref<DraftExtraction | null>(null);
const saveState = ref<'idle' | 'saved'>('idle');

const confidenceTone: Record<DraftConfidence, string> = {
  high: 'bg-emerald-50 text-emerald-700',
  medium: 'bg-amber-50 text-amber-700',
  low: 'bg-rose-50 text-rose-700',
};

const confidenceLabel: Record<DraftConfidence, string> = {
  high: '高置信',
  medium: '待确认',
  low: '低置信',
};

const sourceSummary = computed(() => {
  const normalized = inputText.value.trim().replace(/\s+/g, ' ');
  if (!normalized) {
    return '还没有输入待提取的文本';
  }

  return normalized.length > 96 ? `${normalized.slice(0, 96)}...` : normalized;
});

const formatDateLabel = (value: string) => {
  if (!value) {
    return '待补充';
  }

  const date = new Date(`${value}T00:00:00`);
  if (Number.isNaN(date.getTime())) {
    return '待补充';
  }

  return new Intl.DateTimeFormat('zh-CN', {
    month: 'long',
    day: 'numeric',
    weekday: 'long',
  }).format(date);
};

const buildFallbackDate = () => {
  const date = new Date();
  date.setDate(date.getDate() + 14);

  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, '0');
  const day = `${date.getDate()}`.padStart(2, '0');

  return `${year}-${month}-${day}`;
};

const extractDate = (text: string) => {
  const explicit = text.match(/(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})/);
  if (explicit) {
    const [, year, month, day] = explicit;
    return {
      value: `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`,
      confidence: 'high' as const,
    };
  }

  const partial = text.match(/(\d{1,2})月(\d{1,2})日/);
  if (partial) {
    const year = new Date().getFullYear();
    const [, month, day] = partial;

    return {
      value: `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`,
      confidence: 'medium' as const,
    };
  }

  return {
    value: buildFallbackDate(),
    confidence: 'low' as const,
  };
};

const extractTimes = (text: string) => {
  const matches = [...text.matchAll(/\b([01]?\d|2[0-3]):([0-5]\d)\b/g)].map((match) => match[0]);

  return {
    departureTime: {
      value: matches[0] ?? '09:30',
      confidence: matches[0] ? ('high' as const) : ('low' as const),
    },
    arrivalTime: {
      value: matches[1] ?? '11:45',
      confidence: matches[1] ? ('high' as const) : ('medium' as const),
    },
  };
};

const extractRoute = (text: string) => {
  const routeMatch = text.match(/([\u4e00-\u9fa5]{2,8})\s*(?:飞|到|->|→|-)\s*([\u4e00-\u9fa5]{2,8})/);
  if (routeMatch) {
    return {
      origin: {value: routeMatch[1], confidence: 'high' as const},
      destination: {value: routeMatch[2], confidence: 'high' as const},
    };
  }

  return {
    origin: {value: '北京', confidence: 'low' as const},
    destination: {value: '上海', confidence: 'low' as const},
  };
};

const derivePackingItems = (text: string) => {
  const candidates = [
    {keyword: '身份证', label: '身份证'},
    {keyword: '护照', label: '护照'},
    {keyword: '充电宝', label: '充电宝'},
    {keyword: '雨伞', label: '雨伞'},
    {keyword: '外套', label: '薄外套'},
  ];

  const matched = candidates
    .filter((item) => text.includes(item.keyword))
    .map((item) => ({label: item.label, checked: true}));

  return matched.length
    ? matched
    : [
        {label: '身份证', checked: true},
        {label: '充电宝', checked: true},
        {label: '换洗衣物', checked: false},
      ];
};

const createDraftFromInput = (rawText: string): DraftExtraction => {
  const text = rawText.trim();
  const date = extractDate(text);
  const times = extractTimes(text);
  const route = extractRoute(text);
  const flightNo = text.match(/\b([A-Z]{2}\d{3,4})\b/i)?.[1]?.toUpperCase() ?? '待补充';
  const hotelMatch = text.match(/(?:入住|酒店|民宿)([^。\n]+)/);
  const destinationName = route.destination.value;
  const warnings: string[] = [];

  if (flightNo === '待补充') {
    warnings.push('没有识别到明确的航班号，建议用户确认交通班次。');
  }

  if (date.confidence !== 'high') {
    warnings.push('出发日期不是完整结构化信息，当前为推测值。');
  }

  if (!hotelMatch) {
    warnings.push('没有识别到明确酒店信息，确认页里保留为空。');
  }

  return {
    tripTitle: {
      value: `${destinationName}行程草稿`,
      confidence: route.destination.confidence === 'high' ? 'medium' : 'low',
    },
    travelDate: date,
    departureTime: times.departureTime,
    arrivalTime: times.arrivalTime,
    origin: route.origin,
    destination: route.destination,
    reference: {
      value: flightNo,
      confidence: flightNo === '待补充' ? 'low' : 'high',
    },
    hotel: {
      value: hotelMatch ? hotelMatch[1].replace(/[，。,]/g, '').trim() : '',
      confidence: hotelMatch ? 'medium' : 'low',
    },
    packingItems: derivePackingItems(text),
    warnings,
  };
};

const resetDraft = () => {
  draft.value = null;
  saveState.value = 'idle';
};

const handleExtract = () => {
  if (!inputText.value.trim()) {
    return;
  }

  saveState.value = 'idle';
  isExtracting.value = true;

  window.setTimeout(() => {
    draft.value = createDraftFromInput(inputText.value);
    isExtracting.value = false;
  }, 1200);
};

const handleSave = () => {
  if (!draft.value) {
    return;
  }

  saveState.value = 'saved';
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
          <p class="text-sm text-outline">先把文本提取确认流跑通，帮助用户把碎片化出行信息整理成结构化草稿。</p>
        </div>
      </div>
    </section>

    <section class="space-y-4">
      <div class="group relative">
        <textarea
          v-model="inputText"
          class="min-h-[180px] w-full resize-none rounded-2xl border-2 border-pink-100 bg-white p-6 text-zinc-800 shadow-[0_8px_24px_rgba(0,0,0,0.04)] transition-all duration-300 focus:border-primary focus:ring-4 focus:ring-primary/10"
          placeholder="在此粘贴航班、酒店或活动信息..."
        />
        <div class="absolute bottom-4 right-4 flex gap-2">
          <button class="flex items-center gap-2 rounded-full bg-secondary-fixed px-4 py-2 text-sm font-bold text-secondary opacity-70 shadow-[0_4px_12px_rgba(124,82,170,0.2)]" type="button" disabled>
            <ImageIcon :size="16" />
            图片版二期
          </button>
        </div>
      </div>

      <div class="rounded-2xl border border-pink-100 bg-white/80 p-4 text-sm text-outline shadow-[0_4px_16px_rgba(0,0,0,0.03)]">
        <p class="font-bold text-zinc-800">当前输入摘要</p>
        <p class="mt-2 leading-6">{{ sourceSummary }}</p>
      </div>

      <button
        class="flex w-full items-center justify-center gap-3 rounded-full bg-primary py-4 text-lg font-bold text-white shadow-[0_8px_24px_rgba(224,64,160,0.3)] transition-all duration-300 hover:scale-[1.02] active:scale-95 disabled:cursor-not-allowed disabled:opacity-70"
        type="button"
        :disabled="isExtracting || !inputText.trim()"
        @click="handleExtract"
      >
        <Sparkles v-if="!isExtracting" :size="24" />
        <Sparkles v-else :size="24" class="animate-spin" />
        {{ isExtracting ? '正在模拟提取...' : '开始智能提取' }}
      </button>
    </section>

    <Transition name="fade-up">
      <section v-if="draft" class="space-y-4">
        <div class="flex items-center justify-between gap-4">
          <div>
            <h3 class="px-2 text-lg font-bold text-zinc-900">提取确认页</h3>
            <p class="px-2 text-sm text-outline">这里模拟 MVP 的“提取后人工确认再保存”流程。</p>
          </div>
          <span class="rounded-full bg-tertiary-fixed px-3 py-1 text-xs font-bold uppercase tracking-wider text-tertiary">待确认</span>
        </div>

        <div v-if="saveState === 'saved'" class="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          <CheckCircle2 :size="18" />
          已完成 mock 保存，下一步可以把这份草稿接到真实 Trip / DayPlan / Activity store。
        </div>

        <div v-if="draft.warnings.length" class="rounded-2xl border border-amber-100 bg-amber-50 p-4">
          <div class="mb-3 flex items-center gap-2 text-amber-700">
            <TriangleAlert :size="18" />
            <span class="text-sm font-bold">需要人工确认的字段</span>
          </div>
          <ul class="space-y-2 text-sm text-amber-800">
            <li v-for="warning in draft.warnings" :key="warning">{{ warning }}</li>
          </ul>
        </div>

        <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div class="rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_8px_20px_rgba(224,64,160,0.08)]">
            <div class="mb-3 flex items-center gap-2 text-primary">
              <Edit3 :size="18" />
              <span class="text-xs font-bold uppercase tracking-tight">行程标题</span>
            </div>
            <input v-model="draft.tripTitle.value" class="w-full rounded-xl border border-pink-100 px-4 py-3 font-bold text-zinc-900 focus:border-primary focus:outline-none" type="text">
            <span class="mt-3 inline-flex rounded-full px-2 py-1 text-[11px] font-bold" :class="confidenceTone[draft.tripTitle.confidence]">
              {{ confidenceLabel[draft.tripTitle.confidence] }}
            </span>
          </div>

          <div class="rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_8px_20px_rgba(224,64,160,0.08)]">
            <div class="mb-3 flex items-center gap-2 text-primary">
              <CalendarIcon :size="18" />
              <span class="text-xs font-bold uppercase tracking-tight">日期</span>
            </div>
            <input v-model="draft.travelDate.value" class="w-full rounded-xl border border-pink-100 px-4 py-3 font-bold text-zinc-900 focus:border-primary focus:outline-none" type="date">
            <p class="mt-2 text-sm text-outline">{{ formatDateLabel(draft.travelDate.value) }}</p>
            <span class="mt-3 inline-flex rounded-full px-2 py-1 text-[11px] font-bold" :class="confidenceTone[draft.travelDate.confidence]">
              {{ confidenceLabel[draft.travelDate.confidence] }}
            </span>
          </div>

          <div class="rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_8px_20px_rgba(224,64,160,0.08)]">
            <div class="mb-3 flex items-center gap-2 text-tertiary">
              <Clock :size="18" />
              <span class="text-xs font-bold uppercase tracking-tight">时间</span>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <input v-model="draft.departureTime.value" class="rounded-xl border border-pink-100 px-4 py-3 font-bold text-zinc-900 focus:border-primary focus:outline-none" type="time">
              <input v-model="draft.arrivalTime.value" class="rounded-xl border border-pink-100 px-4 py-3 font-bold text-zinc-900 focus:border-primary focus:outline-none" type="time">
            </div>
            <div class="mt-3 flex gap-2">
              <span class="inline-flex rounded-full px-2 py-1 text-[11px] font-bold" :class="confidenceTone[draft.departureTime.confidence]">
                出发 {{ confidenceLabel[draft.departureTime.confidence] }}
              </span>
              <span class="inline-flex rounded-full px-2 py-1 text-[11px] font-bold" :class="confidenceTone[draft.arrivalTime.confidence]">
                到达 {{ confidenceLabel[draft.arrivalTime.confidence] }}
              </span>
            </div>
          </div>

          <div class="rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_8px_20px_rgba(224,64,160,0.08)]">
            <div class="mb-3 flex items-center gap-2 text-secondary">
              <Plane :size="18" />
              <span class="text-xs font-bold uppercase tracking-tight">交通</span>
            </div>
            <div class="grid grid-cols-2 gap-3">
              <input v-model="draft.origin.value" class="rounded-xl border border-pink-100 px-4 py-3 font-bold text-zinc-900 focus:border-primary focus:outline-none" type="text" placeholder="出发地">
              <input v-model="draft.destination.value" class="rounded-xl border border-pink-100 px-4 py-3 font-bold text-zinc-900 focus:border-primary focus:outline-none" type="text" placeholder="目的地">
            </div>
            <input v-model="draft.reference.value" class="mt-3 w-full rounded-xl border border-pink-100 px-4 py-3 font-bold text-zinc-900 focus:border-primary focus:outline-none" type="text" placeholder="航班号 / 车次">
            <span class="mt-3 inline-flex rounded-full px-2 py-1 text-[11px] font-bold" :class="confidenceTone[draft.reference.confidence]">
              {{ confidenceLabel[draft.reference.confidence] }}
            </span>
          </div>

          <div class="rounded-2xl border border-pink-50 bg-white p-5 shadow-[0_8px_20px_rgba(224,64,160,0.08)] md:col-span-2">
            <div class="mb-3 flex items-center gap-2 text-secondary">
              <MapPin :size="18" />
              <span class="text-xs font-bold uppercase tracking-tight">酒店 / 落脚点</span>
            </div>
            <input v-model="draft.hotel.value" class="w-full rounded-xl border border-pink-100 px-4 py-3 font-bold text-zinc-900 focus:border-primary focus:outline-none" type="text" placeholder="例如 静安嘉里酒店">
            <span class="mt-3 inline-flex rounded-full px-2 py-1 text-[11px] font-bold" :class="confidenceTone[draft.hotel.confidence]">
              {{ confidenceLabel[draft.hotel.confidence] }}
            </span>
          </div>

          <div class="rounded-2xl border-2 border-dashed border-secondary/20 bg-secondary-fixed/30 p-5 md:col-span-2">
            <div class="mb-4 flex items-center gap-2 text-secondary">
              <ListChecks :size="20" />
              <span class="text-xs font-bold uppercase tracking-tight">准备清单</span>
            </div>
            <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <label v-for="item in draft.packingItems" :key="item.label" class="group flex cursor-pointer items-center gap-3 rounded-full bg-white/60 p-3">
                <input v-model="item.checked" class="h-5 w-5 rounded-full border-secondary text-secondary focus:ring-secondary/20" type="checkbox">
                <span class="text-sm font-medium text-zinc-800">{{ item.label }}</span>
              </label>
            </div>
          </div>
        </div>

        <div class="flex gap-4 pt-2">
          <button class="flex flex-1 items-center justify-center gap-2 rounded-full bg-surface-variant py-4 font-bold text-zinc-800 transition-colors hover:bg-outline-variant" type="button" @click="resetDraft">
            <Trash2 :size="20" />
            放弃
          </button>
          <button class="bouncy-hover candy-shadow-tertiary flex flex-[2] items-center justify-center gap-2 rounded-full bg-tertiary py-4 font-bold text-white" type="button" @click="handleSave">
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
