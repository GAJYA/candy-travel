<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'

onLaunch(() => {
  console.log('App Launch')
})
</script>

<style lang="scss">
/* 全局基础：所有页面继承的字体 / 背景 */
page {
  background: $candy-background;
  color: $candy-on-background;
  font-size: $candy-font-body-lg;
  line-height: 1.6;
  font-family: "DM Sans", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
}

/* 通用类：可在任意 vue 文件用，无需重复定义 */
.candy-card {
  background: $candy-surface-container-lowest;
  border-radius: $candy-radius-md;
  padding: $candy-space-md;
  box-shadow: $candy-shadow-card;
  border: 2rpx solid rgba(255, 255, 255, 0.72);
}

.candy-card--tinted {
  background: $candy-surface-container;
}

.candy-pill {
  border-radius: $candy-radius-full;
}

.candy-btn {
  border-radius: $candy-radius-full;
  font-size: $candy-font-body-lg;
  font-weight: 600;
  line-height: 1.5;
  padding: 24rpx $candy-space-lg;
  border: none;
  text-align: center;
}
.candy-btn--primary {
  background: $candy-primary;
  color: $candy-on-primary;
  box-shadow: $candy-shadow-primary;
}
.candy-btn--primary[disabled] {
  background: $candy-outline-variant;
  color: $candy-on-surface-variant;
  box-shadow: none;
}
.candy-btn--ghost {
  background: $candy-surface-container-lowest;
  color: $candy-on-surface;
  border: 2rpx solid $candy-outline-variant;
  box-shadow: none;
}

.candy-input {
  background: $candy-surface-container-lowest;
  border: 2rpx solid $candy-outline-variant;
  border-radius: $candy-radius-full;
  padding: 20rpx 32rpx;
  font-size: $candy-font-body-lg;
  color: $candy-on-surface;
}
.candy-input:focus {
  border-color: $candy-primary;
}

.candy-tag {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 24rpx;
  border-radius: $candy-radius-full;
  background: $candy-primary-fixed;
  color: $candy-on-primary-fixed-variant;
  font-size: $candy-font-label-md;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.candy-text-muted {
  color: $candy-on-surface-variant;
}
.candy-text-error {
  color: $candy-error;
}
</style>
