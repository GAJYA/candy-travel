<template>
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
      <view class="bottom-nav__icon" :class="`bottom-nav__icon--${item.key}`">
        <view class="icon-line icon-line--a" />
        <view class="icon-line icon-line--b" />
        <view class="icon-line icon-line--c" />
        <view class="icon-line icon-line--d" />
      </view>
      <text class="bottom-nav__label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
type NavKey = 'home' | 'calendar' | 'ai' | 'profile' | 'trip'

interface NavItem {
  key: NavKey
  label: string
  url?: string
  disabled?: boolean
}

const props = defineProps<{
  active?: NavKey
  beforeNavigate?: (key: NavKey) => boolean | Promise<boolean>
}>()

const items: NavItem[] = [
  { key: 'home', label: '首页', url: '/pages/index/index' },
  { key: 'calendar', label: '日历', disabled: true },
  { key: 'ai', label: 'AI助手', disabled: true },
  { key: 'profile', label: '我的', disabled: true },
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
  position: relative;
  width: 40rpx;
  height: 40rpx;
  color: currentColor;
}

.icon-line {
  position: absolute;
  box-sizing: border-box;
  border-color: currentColor;
}

.bottom-nav__icon--home .icon-line--a {
  left: 6rpx;
  top: 16rpx;
  width: 28rpx;
  height: 20rpx;
  border-left: 5rpx solid currentColor;
  border-right: 5rpx solid currentColor;
  border-bottom: 5rpx solid currentColor;
  border-radius: 0 0 5rpx 5rpx;
}

.bottom-nav__icon--home .icon-line--b {
  left: 8rpx;
  top: 5rpx;
  width: 24rpx;
  height: 24rpx;
  border-left: 5rpx solid currentColor;
  border-top: 5rpx solid currentColor;
  border-radius: 4rpx;
  transform: rotate(45deg);
}

.bottom-nav__icon--calendar .icon-line--a {
  left: 6rpx;
  top: 8rpx;
  width: 28rpx;
  height: 28rpx;
  border: 4rpx solid currentColor;
  border-radius: 7rpx;
}

.bottom-nav__icon--calendar .icon-line--b {
  left: 10rpx;
  right: 10rpx;
  top: 17rpx;
  height: 4rpx;
  border-radius: $candy-radius-full;
  background: currentColor;
}

.bottom-nav__icon--calendar .icon-line--c,
.bottom-nav__icon--calendar .icon-line--d {
  top: 4rpx;
  width: 4rpx;
  height: 10rpx;
  border-radius: $candy-radius-full;
  background: currentColor;
}

.bottom-nav__icon--calendar .icon-line--c {
  left: 14rpx;
}

.bottom-nav__icon--calendar .icon-line--d {
  right: 14rpx;
}

.bottom-nav__icon--ai .icon-line--a {
  left: 15rpx;
  top: 3rpx;
  width: 10rpx;
  height: 34rpx;
  border-radius: $candy-radius-full;
  background: currentColor;
}

.bottom-nav__icon--ai .icon-line--b {
  left: 3rpx;
  top: 15rpx;
  width: 34rpx;
  height: 10rpx;
  border-radius: $candy-radius-full;
  background: currentColor;
}

.bottom-nav__icon--ai .icon-line--c {
  right: 1rpx;
  top: 1rpx;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.72;
}

.bottom-nav__icon--ai .icon-line--d {
  left: 1rpx;
  bottom: 3rpx;
  width: 6rpx;
  height: 6rpx;
  border-radius: 50%;
  background: currentColor;
  opacity: 0.54;
}

.bottom-nav__icon--profile .icon-line--a {
  left: 14rpx;
  top: 5rpx;
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: currentColor;
}

.bottom-nav__icon--profile .icon-line--b {
  left: 8rpx;
  bottom: 5rpx;
  width: 24rpx;
  height: 16rpx;
  border-radius: 16rpx 16rpx 6rpx 6rpx;
  background: currentColor;
}

.bottom-nav__label {
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.2;
}
</style>
