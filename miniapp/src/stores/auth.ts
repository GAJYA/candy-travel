import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi, type UserInfo } from '../services/auth'
import { ApiRequestError, setUnauthorizedHandler, tokenStorage } from '../services/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<UserInfo | null>(null)
  const loading = ref(false)
  const error = ref<string>('')
  const isAuthenticated = computed(() => user.value !== null)

  const clear = () => {
    user.value = null
    tokenStorage.clear()
  }

  // 让 api.ts 收到 401 时回调到这里
  setUnauthorizedHandler(() => {
    user.value = null
  })

  /** 启动时尝试用已有 token 拉 user，401 会被拦截器自动清掉 */
  const bootstrap = async () => {
    if (!tokenStorage.get()) return
    loading.value = true
    error.value = ''
    try {
      user.value = await authApi.me()
    } catch (e) {
      // token 失效或网络错误：保持未登录态
      if (!(e instanceof ApiRequestError) || e.statusCode !== 401) {
        error.value = formatError(e)
      }
      user.value = null
    } finally {
      loading.value = false
    }
  }

  const login = async () => {
    loading.value = true
    error.value = ''
    try {
      const result = await authApi.login()
      tokenStorage.set(result.token)
      user.value = result.user
    } catch (e) {
      error.value = formatError(e)
      throw e
    } finally {
      loading.value = false
    }
  }

  const updateProfile = async (
    payload: Partial<Pick<UserInfo, 'nickname' | 'avatarUrl' | 'locale' | 'timezone'>>
  ) => {
    const nextUser = await authApi.patchMe(payload)
    user.value = nextUser
    return nextUser
  }

  const logout = () => {
    clear()
  }

  return { user, loading, error, isAuthenticated, bootstrap, login, updateProfile, logout }
})

const formatError = (e: unknown): string => {
  if (e instanceof ApiRequestError) return `[${e.statusCode}] ${e.message}`
  if (e instanceof Error) return e.message
  return String(e)
}
