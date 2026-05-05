import { request } from './api'

export type TripStatus = 'draft' | 'planning' | 'confirmed' | 'completed' | 'archived'
export type TransportMode = 'flight' | 'train' | 'bus' | 'car'

export interface Trip {
  id: string
  title: string
  destinationCity: string | null
  status: TripStatus
  startDate: string | null
  endDate: string | null
  coverImageUrl: string | null
  note: string | null
  timezone: string
  createdVia: 'manual' | 'ai_import'
  createdAt: string
  updatedAt: string
}

export interface TransportSummary {
  eventId: string
  mode: TransportMode | null
  departAt: string | null
  arriveAt: string | null
  fromCity?: string | null
  toCity?: string | null
  flightNo?: string | null
  trainNo?: string | null
  seat?: string | null
  refCode?: string | null
}

export interface StaySummary {
  eventId: string
  hotelName: string | null
  checkinAt: string | null
  checkoutAt: string | null
  address?: string | null
  roomType?: string | null
  refCode?: string | null
  guests?: number | null
}

export interface TripDetail extends Trip {
  summary: {
    transport: TransportSummary | null
    stay: StaySummary | null
  }
}

export interface TripCreatePayload {
  title: string
  destinationCity?: string
  startDate?: string
  endDate?: string
  note?: string
  timezone?: string
}

export interface TripSummaryPatch {
  title?: string
  destinationCity?: string | null
  note?: string | null
  startDate?: string | null
  endDate?: string | null
  status?: TripStatus
  /** undefined 不动；null 软删；object upsert */
  transport?: Partial<TransportSummary> | null
  /** undefined 不动；null 软删；object upsert */
  stay?: Partial<StaySummary> | null
}

export const tripApi = {
  list: () => request<Trip[]>('/trips'),
  create: (payload: TripCreatePayload) =>
    request<Trip>('/trips', { method: 'POST', data: payload }),
  get: (id: string) => request<TripDetail>(`/trips/${id}`),
  patchSummary: (id: string, payload: TripSummaryPatch) =>
    request<TripDetail>(`/trips/${id}/summary`, { method: 'PATCH', data: payload }),
  delete: (id: string) =>
    request<void>(`/trips/${id}`, { method: 'DELETE' }),
}
