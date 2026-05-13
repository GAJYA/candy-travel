import { apiBaseUrl, request, tokenStorage } from './api'
import type { TripEvent } from './trip-event'

export type AiEventConfidence = 'high' | 'medium' | 'low'
export type AiEventType = 'transport' | 'stay' | 'activity' | 'reminder'

export interface AiTripEventCandidate {
  clientId: string
  eventType: AiEventType
  title: string
  startAt: string | null
  endAt: string | null
  locationName: string | null
  address: string | null
  note: string | null
  meta: Record<string, unknown>
  confidence: AiEventConfidence
  warnings: string[]
  sortOrder: number
}

export interface AiExtractEventsResponse {
  tripId: string
  model: string
  events: AiTripEventCandidate[]
  warnings: string[]
}

const uploadOneImage = (tripId: string, filePath: string): Promise<AiExtractEventsResponse> => {
  const token = tokenStorage.get()
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: `${apiBaseUrl}/trips/${tripId}/ai/extract-events`,
      filePath,
      name: 'images',
      header: token ? { Authorization: `Bearer ${token}` } : {},
      formData: {},
      success: (res) => {
        const status = res.statusCode ?? 0
        if (status >= 200 && status < 300) {
          try {
            resolve(JSON.parse(res.data) as AiExtractEventsResponse)
          } catch {
            reject(new Error('识别结果解析失败'))
          }
          return
        }
        reject(new Error(`识别失败：HTTP ${status}`))
      },
      fail: (err) => reject(new Error(err.errMsg || '图片上传失败')),
    })
  })
}

export const aiImportApi = {
  async extractTripEvents(tripId: string, filePaths: string[]): Promise<AiExtractEventsResponse> {
    const responses: AiExtractEventsResponse[] = []
    for (const filePath of filePaths) {
      responses.push(await uploadOneImage(tripId, filePath))
    }
    return {
      tripId,
      model: responses[0]?.model || 'gpt-5.5',
      events: responses.flatMap((response, responseIndex) => (
        response.events.map((event, eventIndex) => ({
          ...event,
          clientId: `${event.clientId}-${responseIndex}-${eventIndex}`,
          sortOrder: event.sortOrder ?? eventIndex,
        }))
      )),
      warnings: responses.flatMap((response) => response.warnings || []),
    }
  },

  importTripEvents: (tripId: string, events: AiTripEventCandidate[]) =>
    request<TripEvent[]>(`/trips/${tripId}/ai/import-events`, {
      method: 'POST',
      data: { events },
    }),
}
