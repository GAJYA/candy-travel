<template>
  <view class="bottom-nav__safe-zone" />
  <view class="bottom-nav">
    <view
      v-for="item in items"
      :key="item.key"
      class="bottom-nav__item"
      :class="{
        'bottom-nav__item--active': item.key === active,
        'bottom-nav__item--disabled': item.disabled,
      }"
      @click="onTap(item)"
    >
      <CandyIcon class="bottom-nav__icon" :name="item.icon" />
      <text class="bottom-nav__label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import CandyIcon from './CandyIcon.vue'

type NavKey = 'home' | 'calendar' | 'ai' | 'profile' | 'trip'

interface NavItem {
  key: NavKey
  icon: string
  label: string
  url?: string
  disabled?: boolean
}

const props = defineProps<{
  active?: NavKey
  beforeNavigate?: (key: NavKey) => boolean | Promise<boolean>
}>()

const items: NavItem[] = [
  { key: 'home', icon: 'home', label: '首页', url: '/pages/index/index' },
  { key: 'calendar', icon: 'calendar', label: '日历', url: '/pages/calendar/index' },
  { key: 'ai', icon: 'ai', label: 'AI助手', disabled: true },
  { key: 'profile', icon: 'user', label: '我的', url: '/pages/profile/index' },
]

const onTap = async (item: NavItem) => {
  if (item.disabled || !item.url) {
    uni.showToast({ title: '暂未开放', icon: 'none' })
    return
  }
  if (props.beforeNavigate && !(await props.beforeNavigate(item.key))) return
  uni.redirectTo({ url: item.url })
}
</script>

<style lang="scss">
.bottom-nav__safe-zone {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 19;
  height: calc(220rpx + env(safe-area-inset-bottom));
  pointer-events: none;
  background: linear-gradient(180deg, rgba(255, 247, 251, 0), $candy-background 42rpx, $candy-background 100%);
}

.bottom-nav {
  position: fixed;
  left: $candy-gutter;
  right: $candy-gutter;
  bottom: calc(24rpx + env(safe-area-inset-bottom));
  z-index: 20;
  height: 128rpx;
  padding: 12rpx 14rpx;
  border-radius: 56rpx;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid rgba(255, 255, 255, 0.86);
  box-shadow: 0 18rpx 54rpx rgba(96, 72, 104, 0.18);
}

.bottom-nav__item {
  min-width: 0;
  height: 104rpx;
  border-radius: 48rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
  color: rgba(96, 72, 104, 0.54);
}

.bottom-nav__item--active {
  color: $candy-primary;
  background: $candy-primary-fixed;
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.72);
}

.bottom-nav__item--disabled {
  opacity: 0.62;
}

.bottom-nav__icon {
  width: 38rpx;
  height: 38rpx;
  font-size: 38rpx;
  color: currentColor;
}

.bottom-nav__label {
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.2;
}
</style>
