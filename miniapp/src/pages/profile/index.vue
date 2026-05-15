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

      <view class="wishlist-card">
        <view class="wishlist-head">
          <view>
            <text class="settings-title">灵感暂存</text>
            <text class="wishlist-subtitle">把临时起意、种草目的地和以后想去的地方先收起来</text>
          </view>
          <view class="wishlist-count">
            <text>{{ wishlist.length }}</text>
          </view>
        </view>

        <view class="wishlist-tabs">
          <button
            v-for="option in wishlistTypeOptions"
            :key="option.value"
            class="wishlist-tab"
            :class="{ 'wishlist-tab--active': wishlistDraft.type === option.value }"
            @click="wishlistDraft.type = option.value"
          >
            {{ option.label }}
          </button>
        </view>

        <view class="wishlist-form">
          <view class="wishlist-field">
            <input
              class="wishlist-input"
              v-model="wishlistDraft.destination"
              maxlength="32"
              placeholder="想去哪里？如 杭州 / 新西兰"
              confirm-type="done"
            />
          </view>
          <textarea
            class="wishlist-note"
            v-model="wishlistDraft.note"
            maxlength="80"
            placeholder="为什么想去？预算、季节、刷到的灵感都可以记一笔"
            auto-height
          />
          <textarea
            class="wishlist-note wishlist-share"
            v-model="sharedPostText"
            maxlength="1200"
            placeholder="粘贴小红书帖子链接或分享文案，我会帮你整理成一份大概计划"
            auto-height
          />
          <view class="wishlist-row">
            <button
              class="wishlist-add"
              :disabled="!canAddWishlist"
              @click="addWishlistItem"
            >
              保存
            </button>
            <button
              class="wishlist-add wishlist-add--ai"
              :disabled="!canExtractShare || extractingShare"
              @click="createFromSharedPost"
            >
              {{ extractingShare ? '整理中' : '整理并保存' }}
            </button>
          </view>
        </view>

        <view v-if="wishlistLoading" class="wishlist-empty">
          <text class="wishlist-empty__title">正在同步灵感</text>
          <text class="wishlist-empty__hint">从后台取回你之前暂存的目的地。</text>
        </view>

        <view v-else-if="wishlist.length === 0" class="wishlist-empty">
          <text class="wishlist-empty__title">还没有暂存灵感</text>
          <text class="wishlist-empty__hint">下次刷到想去的城市、海岛、国家，就先丢进这里。</text>
        </view>

        <view v-else class="wishlist-list">
          <view
            v-for="item in visibleWishlist"
            :key="item.id"
            class="wish-item"
            :class="{ 'wish-item--done': item.status === 'planned' }"
          >
            <view class="wish-item__main">
              <view class="wish-item__top">
                <text class="wish-type" :class="`wish-type--${item.type}`">{{ typeLabel(item.type) }}</text>
                <text v-if="item.sourceUrl" class="wish-source">来自分享</text>
              </view>
              <text class="wish-destination">{{ item.destination }}</text>
              <text v-if="item.note" class="wish-note">{{ item.note }}</text>
            </view>
            <view v-if="expandedWishlistId === item.id" class="wish-detail">
              <text class="wish-detail__title">计划详情</text>
              <text class="wish-detail__body">{{ item.planDetail || '还没有详细计划。你可以粘贴帖子链接生成，或之后再补充。' }}</text>
            </view>
            <view class="wish-actions">
              <button class="wish-action" @click="toggleWishlistDetail(item.id)">
                {{ expandedWishlistId === item.id ? '收起' : '详情' }}
              </button>
              <button class="wish-action" @click="toggleWishlistStatus(item.id)">
                {{ item.status === 'planned' ? '恢复' : '已计划' }}
              </button>
              <button class="wish-action wish-action--delete" @click="removeWishlistItem(item.id)">删除</button>
            </view>
          </view>
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
import {
  inspirationApi,
  type Inspiration,
  type InspirationStatus,
  type InspirationType,
} from '../../services/inspiration'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const nicknameDraft = ref('')
const nicknameSaving = ref(false)
const LEGACY_WISHLIST_STORAGE_KEY = 'candy-travel:wishlist:v1'

const wishlistTypeOptions: Array<{ label: string; value: InspirationType }> = [
  { label: '短途', value: 'short' },
  { label: '长期', value: 'long' },
]
const wishlist = ref<Inspiration[]>([])
const wishlistLoading = ref(false)
const extractingShare = ref(false)
const expandedWishlistId = ref<string | null>(null)
const sharedPostText = ref('')
const wishlistDraft = ref({
  destination: '',
  type: 'short' as InspirationType,
  note: '',
})

const currentNickname = computed(() => auth.user?.nickname?.trim() || '')
const subtitle = computed(() => (
  auth.isAuthenticated ? '设置同行昵称' : '登录后设置昵称'
))
const nicknameDirty = computed(() => nicknameDraft.value.trim() !== currentNickname.value)
const canSaveNickname = computed(() => (
  !nicknameSaving.value && nicknameDirty.value && Boolean(nicknameDraft.value.trim())
))
const canAddWishlist = computed(() => Boolean(wishlistDraft.value.destination.trim()))
const canExtractShare = computed(() => Boolean(sharedPostText.value.trim()))
const visibleWishlist = computed(() => (
  [...wishlist.value].sort((a, b) => {
    if (a.status !== b.status) return a.status === 'idea' ? -1 : 1
    return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  })
))

const syncNickname = () => {
  nicknameDraft.value = currentNickname.value
}

const bootstrap = async () => {
  await auth.bootstrap()
  syncNickname()
  await loadWishlist()
}

const login = async () => {
  try {
    await auth.login()
    syncNickname()
    await loadWishlist()
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

const loadWishlist = async () => {
  if (!auth.isAuthenticated) {
    wishlist.value = []
    return
  }
  wishlistLoading.value = true
  try {
    await migrateLegacyWishlist()
    wishlist.value = await inspirationApi.list()
  } catch {
    uni.showToast({ title: '灵感加载失败', icon: 'none' })
  } finally {
    wishlistLoading.value = false
  }
}

const migrateLegacyWishlist = async () => {
  const raw = uni.getStorageSync(LEGACY_WISHLIST_STORAGE_KEY)
  if (!raw) return

  try {
    const legacyItems = JSON.parse(String(raw)) as Array<{
      destination?: unknown
      type?: unknown
      note?: unknown
    }>
    if (!Array.isArray(legacyItems) || legacyItems.length === 0) {
      uni.removeStorageSync(LEGACY_WISHLIST_STORAGE_KEY)
      return
    }

    await Promise.all(
      legacyItems
        .map((item) => ({
          destination: typeof item.destination === 'string' ? item.destination.trim() : '',
          type: item.type === 'long' ? 'long' : 'short',
          note: typeof item.note === 'string' && item.note.trim() ? item.note.trim() : null,
        }))
        .filter((item) => item.destination)
        .map((item) => inspirationApi.create(item)),
    )
    uni.removeStorageSync(LEGACY_WISHLIST_STORAGE_KEY)
  } catch {
    // 旧本地数据迁移失败时保留原值，下一次进入页面再尝试。
  }
}

const addWishlistItem = async () => {
  const destination = wishlistDraft.value.destination.trim()
  if (!destination) {
    uni.showToast({ title: '先写一个目的地', icon: 'none' })
    return
  }
  try {
    const item = await inspirationApi.create({
      destination,
      type: wishlistDraft.value.type,
      note: wishlistDraft.value.note.trim() || null,
    })
    wishlist.value.unshift(item)
    wishlistDraft.value.destination = ''
    wishlistDraft.value.note = ''
    uni.showToast({ title: '已暂存灵感', icon: 'success' })
  } catch {
    uni.showToast({ title: '暂存失败', icon: 'none' })
  }
}

const createFromSharedPost = async () => {
  const sharedText = sharedPostText.value.trim()
  if (!sharedText) {
    uni.showToast({ title: '先粘贴帖子链接', icon: 'none' })
    return
  }
  extractingShare.value = true
  try {
    const item = await inspirationApi.createFromShare({
      sharedText,
      type: wishlistDraft.value.type,
    })
    wishlist.value.unshift(item)
    sharedPostText.value = ''
    expandedWishlistId.value = item.id
    uni.showToast({ title: '已整理并暂存', icon: 'success' })
  } catch {
    uni.showToast({ title: '整理失败，稍后再试', icon: 'none' })
  } finally {
    extractingShare.value = false
  }
}

const replaceWishlistItem = (item: Inspiration) => {
  wishlist.value = wishlist.value.map((entry) => entry.id === item.id ? item : entry)
}

const toggleWishlistStatus = async (id: string) => {
  const item = wishlist.value.find((entry) => entry.id === id)
  if (!item) return
  const status: InspirationStatus = item.status === 'idea' ? 'planned' : 'idea'
  try {
    replaceWishlistItem(await inspirationApi.patch(id, { status }))
  } catch {
    uni.showToast({ title: '状态更新失败', icon: 'none' })
  }
}

const removeWishlistItem = async (id: string) => {
  try {
    await inspirationApi.delete(id)
    wishlist.value = wishlist.value.filter((entry) => entry.id !== id)
  } catch {
    uni.showToast({ title: '删除失败', icon: 'none' })
  }
}

const toggleWishlistDetail = (id: string) => {
  expandedWishlistId.value = expandedWishlistId.value === id ? null : id
}

const typeLabel = (type: InspirationType) => (type === 'short' ? '短途' : '长期')

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

.settings-card,
.wishlist-card {
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
.wishlist-head {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}
.wishlist-subtitle {
  display: block;
  margin-top: 8rpx;
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  line-height: 1.45;
}
.wishlist-count {
  min-width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: $candy-primary-fixed;
  color: $candy-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $candy-font-body-md;
  font-weight: 900;
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
.wishlist-tabs {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12rpx;
  padding: 8rpx;
  border-radius: $candy-radius-full;
  background: $candy-surface-container-low;
}
.wishlist-tab {
  margin: 0;
  height: 64rpx;
  line-height: 64rpx;
  padding: 0 20rpx;
  border-radius: $candy-radius-full;
  background: transparent;
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  font-weight: 900;
}
.wishlist-tab::after {
  border: none;
}
.wishlist-tab--active {
  background: $candy-on-surface;
  color: $candy-inverse-on-surface;
}
.wishlist-form {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}
.wishlist-field,
.wishlist-note {
  box-sizing: border-box;
  border-radius: $candy-radius-sm;
  background: $candy-surface-container-low;
  border: 2rpx solid $candy-outline-variant;
}
.wishlist-field {
  padding: 16rpx 20rpx;
}
.wishlist-input {
  width: 100%;
  min-height: 54rpx;
  color: $candy-on-surface;
  font-size: $candy-font-body-lg;
  font-weight: 800;
}
.wishlist-row {
  display: grid;
  grid-template-columns: 150rpx 1fr;
  gap: 14rpx;
  align-items: stretch;
}
.wishlist-add {
  margin: 0;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 20rpx;
  border-radius: $candy-radius-full;
  background: $candy-primary;
  color: $candy-on-primary;
  font-size: $candy-font-body-md;
  font-weight: 900;
  box-shadow: 0 10rpx 24rpx rgba(224, 64, 160, 0.18);
}
.wishlist-add::after {
  border: none;
}
.wishlist-add[disabled] {
  opacity: 0.48;
  box-shadow: none;
}
.wishlist-add--ai {
  background: $candy-on-surface;
  color: $candy-inverse-on-surface;
  box-shadow: $candy-shadow-secondary;
}
.wishlist-note {
  width: 100%;
  min-height: 96rpx;
  padding: 18rpx 20rpx;
  color: $candy-on-surface;
  font-size: $candy-font-body-md;
  line-height: 1.45;
}
.wishlist-share {
  min-height: 120rpx;
}
.wishlist-empty {
  padding: 30rpx 24rpx;
  border-radius: $candy-radius-sm;
  background: linear-gradient(135deg, $candy-tertiary-fixed, $candy-primary-fixed);
}
.wishlist-empty__title,
.wishlist-empty__hint {
  display: block;
}
.wishlist-empty__title {
  color: $candy-on-surface;
  font-size: $candy-font-body-md;
  font-weight: 900;
}
.wishlist-empty__hint {
  margin-top: 8rpx;
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  line-height: 1.45;
}
.wishlist-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}
.wish-item {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  padding: 22rpx;
  border-radius: $candy-radius-sm;
  background: $candy-surface-container-low;
  border: 2rpx solid rgba(255, 255, 255, 0.8);
}
.wish-item--done {
  opacity: 0.68;
}
.wish-item__main {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}
.wish-item__top,
.wish-actions {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12rpx;
}
.wish-type,
.wish-source {
  display: inline-flex;
  align-items: center;
  min-height: 40rpx;
  padding: 0 14rpx;
  border-radius: $candy-radius-full;
  font-size: 22rpx;
  font-weight: 900;
}
.wish-type--short {
  background: $candy-tertiary-fixed;
  color: $candy-on-tertiary-fixed;
}
.wish-type--long {
  background: $candy-secondary-fixed;
  color: $candy-on-secondary-fixed;
}
.wish-source {
  background: $candy-surface-container-lowest;
  color: $candy-on-surface-variant;
}
.wish-destination {
  color: $candy-on-surface;
  font-size: 36rpx;
  font-weight: 900;
  line-height: 1.2;
}
.wish-note {
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  line-height: 1.45;
}
.wish-detail {
  padding: 18rpx 20rpx;
  border-radius: $candy-radius-sm;
  background: $candy-surface-container-lowest;
}
.wish-detail__title,
.wish-detail__body {
  display: block;
}
.wish-detail__title {
  color: $candy-on-surface;
  font-size: $candy-font-label-md;
  font-weight: 900;
}
.wish-detail__body {
  margin-top: 8rpx;
  color: $candy-on-surface-variant;
  font-size: $candy-font-label-md;
  line-height: 1.55;
  white-space: pre-wrap;
}
.wish-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
}
.wish-action {
  margin: 0;
  min-width: 132rpx;
  height: 58rpx;
  line-height: 58rpx;
  padding: 0 18rpx;
  border-radius: $candy-radius-full;
  background: $candy-surface-container-lowest;
  color: $candy-on-surface-variant;
  font-size: 22rpx;
  font-weight: 900;
}
.wish-action::after {
  border: none;
}
.wish-action--delete {
  color: $candy-error;
}
</style>
