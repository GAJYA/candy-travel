<template>
  <view class="page">
    <view class="topbar">
      <view>
        <text class="brand">我的</text>
        <text class="subtitle">{{ subtitle }}</text>
      </view>
    </view>

    <view v-if="!auth.isAuthenticated" class="candy-card login-card">
      <view class="login-mark">
        <CandyIcon name="user" />
      </view>
      <text class="login-title">登录后设置昵称</text>
      <text class="login-hint">设置昵称后，同行成员会看到这个名称</text>
      <button class="candy-btn candy-btn--primary login-btn" :disabled="auth.loading" @click="login">
        {{ auth.loading ? '登录中...' : '微信登录' }}
      </button>
      <text v-if="auth.error" class="candy-text-error login-error">{{ auth.error }}</text>
    </view>

    <view v-else class="profile-content">
      <view class="settings-card">
        <text class="settings-title">昵称</text>
        <view class="nickname-field">
          <input
            class="nickname-input"
            v-model="nicknameDraft"
            maxlength="24"
            placeholder="输入你的昵称"
            confirm-type="done"
            @confirm="saveNickname"
          />
        </view>
        <view class="settings-actions">
          <button
            class="profile-btn profile-btn--ghost"
            :disabled="!nicknameDirty || nicknameSaving"
            @click="resetNickname"
          >
            重置
          </button>
          <button
            class="profile-btn profile-btn--primary"
            :disabled="!canSaveNickname"
            @click="saveNickname"
          >
            {{ nicknameSaving ? '保存中...' : '保存昵称' }}
          </button>
        </view>
      </view>
    </view>

    <CandyBottomNav active="profile" />
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import CandyBottomNav from '../../components/CandyBottomNav.vue'
import CandyIcon from '../../components/CandyIcon.vue'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const nicknameDraft = ref('')
const nicknameSaving = ref(false)

const currentNickname = computed(() => auth.user?.nickname?.trim() || '')
const subtitle = computed(() => (
  auth.isAuthenticated ? '设置同行昵称' : '登录后设置昵称'
))
const nicknameDirty = computed(() => nicknameDraft.value.trim() !== currentNickname.value)
const canSaveNickname = computed(() => (
  !nicknameSaving.value && nicknameDirty.value && Boolean(nicknameDraft.value.trim())
))

const syncNickname = () => {
  nicknameDraft.value = currentNickname.value
}

const bootstrap = async () => {
  await auth.bootstrap()
  syncNickname()
}

const login = async () => {
  try {
    await auth.login()
    syncNickname()
  } catch {
    uni.showToast({ title: auth.error || '登录失败', icon: 'none' })
  }
}

const resetNickname = () => {
  syncNickname()
}

const saveNickname = async () => {
  const nickname = nicknameDraft.value.trim()
  if (!nickname) {
    uni.showToast({ title: '请输入昵称', icon: 'none' })
    return
  }
  if (!nicknameDirty.value || nicknameSaving.value) return
  nicknameSaving.value = true
  try {
    await auth.updateProfile({ nickname })
    syncNickname()
    uni.showToast({ title: '昵称已更新', icon: 'success' })
  } catch {
    uni.showToast({ title: '昵称保存失败', icon: 'none' })
  } finally {
    nicknameSaving.value = false
  }
}

watch(currentNickname, syncNickname)

onMounted(() => {
  void bootstrap()
})
onShow(bootstrap)
</script>

<style lang="scss">
.page {
  min-height: 100vh;
  padding: 36rpx $candy-gutter 220rpx;
  padding-bottom: calc(220rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 28rpx;
  background:
    linear-gradient(180deg, rgba(255, 239, 255, 0.9) 0%, rgba(255, 247, 251, 0) 360rpx),
    $candy-background;
}

.topbar {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  padding: $candy-space-xs 0 0;
}
.brand {
  display: block;
  font-size: 54rpx;
  font-weight: 800;
  color: $candy-on-background;
  line-height: 1.1;
}
.subtitle {
  display: block;
  margin-top: 6rpx;
  font-size: $candy-font-body-md;
  color: $candy-on-surface-variant;
}

.login-card,
.profile-content {
  display: flex;
  flex-direction: column;
  gap: $candy-space-sm;
}
.login-card {
  align-items: center;
  padding: $candy-space-md;
  text-align: center;
}
.login-mark {
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  background: $candy-primary-fixed;
  color: $candy-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
}
.login-title {
  color: $candy-on-surface;
  font-size: $candy-font-headline-md;
  font-weight: 800;
}
.login-hint {
  color: $candy-on-surface-variant;
  font-size: $candy-font-body-md;
}
.login-btn {
  width: 100%;
}
.login-error {
  font-size: $candy-font-label-md;
}

.settings-card {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  padding: 28rpx;
  border-radius: $candy-radius-md;
  background: $candy-surface-container-lowest;
  border: 2rpx solid rgba(255, 255, 255, 0.78);
  box-shadow: $candy-shadow-card;
}
.settings-title {
  display: block;
  color: $candy-on-surface;
  font-size: $candy-font-body-lg;
  font-weight: 800;
}
.nickname-field {
  display: flex;
  flex-direction: column;
  padding: 18rpx 22rpx;
  border-radius: $candy-radius-sm;
  background: $candy-surface-container-low;
  border: 2rpx solid $candy-outline-variant;
}
.nickname-input {
  width: 100%;
  box-sizing: border-box;
  min-height: 56rpx;
  color: $candy-on-surface;
  font-size: 36rpx;
  font-weight: 800;
}
.settings-actions {
  display: flex;
  flex-direction: row;
  gap: 16rpx;
}
.profile-btn {
  margin: 0;
  min-width: 0;
  flex: 1;
  height: 76rpx;
  line-height: 76rpx;
  padding: 0 24rpx;
  border-radius: $candy-radius-full;
  font-size: $candy-font-body-md;
  font-weight: 900;
}
.profile-btn::after {
  border: none;
}
.profile-btn--primary {
  background: $candy-primary;
  color: $candy-on-primary;
  box-shadow: 0 10rpx 26rpx rgba(224, 64, 160, 0.18);
}
.profile-btn--ghost {
  background: $candy-surface-container;
  color: $candy-on-surface-variant;
}
.profile-btn[disabled] {
  opacity: 0.52;
  box-shadow: none;
}
</style>
