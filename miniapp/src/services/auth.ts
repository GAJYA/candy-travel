import { request } from './api'

export interface UserInfo {
  id: string
  nickname: string | null
  avatarUrl: string | null
  locale: string
  timezone: string
  createdAt: string
  updatedAt: string
}

export interface LoginResult {
  token: string
  expiresIn: number
  user: UserInfo
}

const wxLogin = (): Promise<string> =>
  new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: (res) => {
        if (res.code) resolve(res.code)
        else reject(new Error('wx.login returned no code'))
      },
      fail: (err) => reject(new Error(err.errMsg || 'wx.login failed')),
    })
  })

export const authApi = {
  /** 完整登录链路：wx.login → 后端换 token */
  login: async (): Promise<LoginResult> => {
    const code = await wxLogin()
    return request<LoginResult>('/auth/wechat/login', {
      method: 'POST',
      data: { code },
      auth: false,
    })
  },
  me: () => request<UserInfo>('/me'),
  patchMe: (payload: Partial<Pick<UserInfo, 'nickname' | 'avatarUrl' | 'locale' | 'timezone'>>) =>
    request<UserInfo>('/me', { method: 'PATCH', data: payload }),
}
