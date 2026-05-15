import { request } from './api'

export type InspirationType = 'short' | 'long'
export type InspirationStatus = 'idea' | 'planned'

export interface Inspiration {
  id: string
  destination: string
  type: InspirationType
  sourceUrl: string | null
  note: string | null
  planDetail: string | null
  status: InspirationStatus
  createdAt: string
  updatedAt: string
}

export interface InspirationCreatePayload {
  destination: string
  type: InspirationType
  note?: string | null
  sourceUrl?: string | null
  planDetail?: string | null
}

export interface InspirationPatchPayload {
  destination?: string
  type?: InspirationType
  note?: string | null
  sourceUrl?: string | null
  planDetail?: string | null
  status?: InspirationStatus
}

export interface InspirationFromSharePayload {
  sharedText: string
  type?: InspirationType
}

export const inspirationApi = {
  list: () => request<Inspiration[]>('/inspirations'),
  create: (payload: InspirationCreatePayload) =>
    request<Inspiration>('/inspirations', { method: 'POST', data: payload }),
  createFromShare: (payload: InspirationFromSharePayload) =>
    request<Inspiration>('/inspirations/from-share', { method: 'POST', data: payload }),
  patch: (id: string, payload: InspirationPatchPayload) =>
    request<Inspiration>(`/inspirations/${id}`, { method: 'PATCH', data: payload }),
  delete: (id: string) =>
    request<void>(`/inspirations/${id}`, { method: 'DELETE' }),
}
