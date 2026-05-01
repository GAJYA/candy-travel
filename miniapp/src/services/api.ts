const DEFAULT_API_BASE_URL = 'http://localhost:8000/api/v1'

const trimTrailingSlash = (s: string) => s.replace(/\/+$/, '')

export const apiBaseUrl = trimTrailingSlash(
  (import.meta.env.VITE_API_BASE_URL as string | undefined) || DEFAULT_API_BASE_URL,
)

const TOKEN_STORAGE_KEY = 'candy_travel_token'

let tokenCache: string | null = null
let onUnauthorized: (() => void) | null = null

export const tokenStorage = {
  get(): string | null {
    if (tokenCache !== null) return tokenCache
    try {
      const stored = uni.getStorageSync(TOKEN_STORAGE_KEY)
      tokenCache = typeof stored === 'string' && stored ? stored : null
    } catch {
      tokenCache = null
    }
    return tokenCache
  },
  set(token: string) {
    tokenCache = token
    uni.setStorageSync(TOKEN_STORAGE_KEY, token)
  },
  clear() {
    tokenCache = null
    uni.removeStorageSync(TOKEN_STORAGE_KEY)
  },
}

export const setUnauthorizedHandler = (fn: () => void) => {
  onUnauthorized = fn
}

export class ApiRequestError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public data?: unknown,
  ) {
    super(message)
    this.name = 'ApiRequestError'
  }
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  data?: unknown
  header?: Record<string, string>
  /** 标记是否需要附带 token；默认 true */
  auth?: boolean
}

const extractMessage = (data: unknown, fallback: string): string => {
  if (data && typeof data === 'object') {
    const d = data as { message?: unknown; detail?: unknown }
    if (typeof d.message === 'string') return d.message
    if (typeof d.detail === 'string') return d.detail
  }
  return fallback
}

export const request = <T>(path: string, options: RequestOptions = {}): Promise<T> => {
  const url = `${apiBaseUrl}${path.startsWith('/') ? path : `/${path}`}`
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.header ?? {}),
  }
  if (options.auth !== false) {
    const token = tokenStorage.get()
    if (token) headers.Authorization = `Bearer ${token}`
  }

  return new Promise((resolve, reject) => {
    uni.request({
      url,
      method: options.method ?? 'GET',
      data: options.data,
      header: headers,
      success: (res) => {
        const status = res.statusCode ?? 0
        if (status >= 200 && status < 300) {
          resolve(res.data as T)
          return
        }
        if (status === 401) {
          tokenStorage.clear()
          onUnauthorized?.()
        }
        reject(
          new ApiRequestError(
            extractMessage(res.data, `HTTP ${status}`),
            status,
            res.data,
          ),
        )
      },
      fail: (err) => {
        reject(new ApiRequestError(err.errMsg || 'request failed', 0, err))
      },
    })
  })
}

export interface HealthzResponse {
  status: 'ok' | 'fail'
  db: 'ok' | 'fail'
  redis: 'ok' | 'fail'
  version: string
  dbError?: string
  redisError?: string
}

export const healthApi = {
  check: () => request<HealthzResponse>('/healthz', { auth: false }),
}
