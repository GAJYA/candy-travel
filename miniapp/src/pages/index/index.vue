<template>
  <view class="page">
    <view class="header">
      <text class="title">CandyTravel</text>
      <text class="subtitle">F1 微信登录 · healthz 探活</text>
    </view>

    <!-- 登录态卡片 -->
    <view class="card">
      <view v-if="auth.isAuthenticated && auth.user" class="user-block">
        <view class="row">
          <text class="label">已登录</text>
          <text class="value ok">{{ auth.user.nickname || '微信用户' }}</text>
        </view>
        <view class="row">
          <text class="label">user id</text>
          <text class="value">{{ auth.user.id }}</text>
        </view>
        <button class="btn ghost" :disabled="auth.loading" @click="logout">退出登录</button>
      </view>

      <view v-else class="login-block">
        <text class="hint">尚未登录，点击下方按钮使用微信登录</text>
        <button class="btn primary" :disabled="auth.loading" @click="login">
          {{ auth.loading ? '登录中…' : '微信登录' }}
        </button>
        <text v-if="auth.error" class="value error">{{ auth.error }}</text>
      </view>
    </view>

    <!-- healthz 卡片 -->
    <view class="card">
      <view class="row">
        <text class="label">API Base</text>
        <text class="value">{{ apiBaseUrl }}</text>
      </view>
      <view class="row">
        <text class="label">状态</text>
        <text class="value" :class="healthStatusClass">{{ healthStatusText }}</text>
      </view>
      <view v-if="health" class="row">
        <text class="label">DB</text>
        <text class="value">{{ health.db }}</text>
      </view>
      <view v-if="health" class="row">
        <text class="label">Redis</text>
        <text class="value">{{ health.redis }}</text>
      </view>
      <view v-if="health" class="row">
        <text class="label">Version</text>
        <text class="value">{{ health.version }}</text>
      </view>
      <view v-if="healthError" class="row">
        <text class="label">Error</text>
        <text class="value error">{{ healthError }}</text>
      </view>
      <button class="btn ghost" :disabled="healthLoading" @click="refreshHealth">
        {{ healthLoading ? '探活中…' : '重新探活' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import {
  ApiRequestError,
  apiBaseUrl,
  healthApi,
  type HealthzResponse,
} from '../../services/api'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()

const health = ref<HealthzResponse | null>(null)
const healthError = ref<string>('')
const healthLoading = ref(false)

const healthStatusText = computed(() => {
  if (healthLoading.value) return '加载中'
  if (healthError.value) return '请求失败'
  if (health.value) return health.value.status
  return '未知'
})

const healthStatusClass = computed(() => {
  if (healthError.value) return 'error'
  if (health.value?.status === 'ok') return 'ok'
  return ''
})

const refreshHealth = async () => {
  healthLoading.value = true
  healthError.value = ''
  try {
    health.value = await healthApi.check()
  } catch (e) {
    if (e instanceof ApiRequestError) {
      healthError.value = `[${e.statusCode}] ${e.message}`
    } else {
      healthError.value = String(e)
    }
    health.value = null
  } finally {
    healthLoading.value = false
  }
}

const login = async () => {
  try {
    await auth.login()
    uni.showToast({ title: '登录成功', icon: 'success' })
  } catch {
    uni.showToast({ title: auth.error || '登录失败', icon: 'none' })
  }
}

const logout = () => {
  auth.logout()
  uni.showToast({ title: '已退出', icon: 'none' })
}

onMounted(async () => {
  await auth.bootstrap()
  await refreshHealth()
})
</script>

<style>
.page {
  padding: 48rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}
.header {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.title {
  font-size: 56rpx;
  font-weight: 600;
}
.subtitle {
  font-size: 26rpx;
  color: #8f8f94;
}
.card {
  background: #f7f7fa;
  border-radius: 16rpx;
  padding: 24rpx 28rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
.user-block,
.login-block {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}
.hint {
  font-size: 26rpx;
  color: #8f8f94;
}
.row {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: center;
}
.label {
  font-size: 26rpx;
  color: #8f8f94;
}
.value {
  font-size: 28rpx;
  color: #1a1a1a;
  max-width: 60%;
  text-align: right;
  word-break: break-all;
}
.value.ok {
  color: #16a34a;
  font-weight: 600;
}
.value.error {
  color: #dc2626;
}
.btn {
  font-size: 30rpx;
  border-radius: 999rpx;
  margin-top: 8rpx;
}
.btn.primary {
  background: #1a1a1a;
  color: #fff;
}
.btn.ghost {
  background: #ffffff;
  color: #1a1a1a;
  border: 2rpx solid #e5e5ea;
}
.btn[disabled] {
  opacity: 0.5;
}
</style>
