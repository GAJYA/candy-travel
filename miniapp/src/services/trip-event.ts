import { request } from './api'

export type TripEventType = 'transport' | 'stay' | 'activity' | 'reminder'
export type TripEventStatus = 'draft' | 'confirmed' | 'canceled'
export type TripEventSource = 'manual' | 'ai_extracted'

export interface TripEvent {
  id: string
  tripId: string
  eventType: TripEventType
  title: string
  startAt: string
  endAt: string | null
  locationName: string | null
  address: string | null
  latitude: number | null
  longitude: number | null
  note: string | null
  meta: {
    icon?: string
    [key: string]: unknown
  }
  status: TripEventStatus
  source: TripEventSource
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export interface TripEventCreatePayload {
  eventType: TripEventType
  title: string
  startAt: string
  endAt?: string | null
  locationName?: string | null
  address?: string | null
  latitude?: number | null
  longitude?: number | null
  note?: string | null
  meta?: Record<string, unknown>
  status?: TripEventStatus
  sortOrder?: number
}

export interface TripEventPatchPayload {
  title?: string
  startAt?: string
  endAt?: string | null
  locationName?: string | null
  address?: string | null
  latitude?: number | null
  longitude?: number | null
  note?: string | null
  meta?: Record<string, unknown>
  status?: TripEventStatus
  sortOrder?: number
}

export const tripEventApi = {
  list: (tripId: string) => request<TripEvent[]>(`/trips/${tripId}/events`),
  create: (tripId: string, payload: TripEventCreatePayload) =>
    request<TripEvent>(`/trips/${tripId}/events`, { method: 'POST', data: payload }),
  patch: (eventId: string, payload: TripEventPatchPayload) =>
    request<TripEvent>(`/events/${eventId}`, { method: 'PATCH', data: payload }),
  delete: (eventId: string) =>
    request<void>(`/events/${eventId}`, { method: 'DELETE' }),
}
