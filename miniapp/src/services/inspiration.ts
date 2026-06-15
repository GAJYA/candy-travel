import { request } from './api'
import type { QuickTripEventCandidate } from './quick-import'

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

export interface InspirationShareDraft {
  destination: string
  sourceUrl: string | null
  note: string | null
  planDetail: string | null
  events: QuickTripEventCandidate[]
}

export type InspirationImportJobStatus = 'pending' | 'running' | 'succeeded' | 'failed' | 'expired'

export interface InspirationImportJob {
  id: string
  status: InspirationImportJobStatus
  result: InspirationShareDraft | null
  errorMessage: string | null
  createdAt: string
  updatedAt: string
  expiresAt: string
  startedAt: string | null
  finishedAt: string | null
}

export const inspirationApi = {
  list: () => request<Inspiration[]>('/inspirations'),
  create: (payload: InspirationCreatePayload) =>
    request<Inspiration>('/inspirations', { method: 'POST', data: payload }),
  createShareImportJob: (payload: InspirationFromSharePayload) =>
    request<InspirationImportJob>('/import-jobs/from-share', {
      method: 'POST',
      data: payload,
    }),
  getImportJob: (id: string) =>
    request<InspirationImportJob>(`/import-jobs/${id}`),
  extractFromShare: (payload: InspirationFromSharePayload) =>
    request<InspirationShareDraft>('/inspirations/from-share/preview', {
      method: 'POST',
      data: payload,
      timeoutMs: 180000,
    }),
  createFromShare: (payload: InspirationFromSharePayload) =>
    request<Inspiration>('/inspirations/from-share', { method: 'POST', data: payload }),
  patch: (id: string, payload: InspirationPatchPayload) =>
    request<Inspiration>(`/inspirations/${id}`, { method: 'PATCH', data: payload }),
  delete: (id: string) =>
    request<void>(`/inspirations/${id}`, { method: 'DELETE' }),
}
