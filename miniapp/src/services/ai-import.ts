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

export type AiImportPhase = 'uploading' | 'recognizing'

export interface AiImportProgress {
  phase: AiImportPhase
  current: number
  total: number
  uploadProgress: number
}

export interface AiImportUploadTask {
  abort: () => void
}

export interface AiImportExtractOptions {
  timeoutMs?: number
  onProgress?: (progress: AiImportProgress) => void
  onUploadTask?: (task: AiImportUploadTask) => void
}

const formatUploadError = (errMsg: string) => {
  if (errMsg.includes('url not in domain list')) {
    return '上传域名未配置：请把 https://www.willer.tech 加到小程序 uploadFile 合法域名'
  }
  if (errMsg.includes('abort')) return '已取消识别'
  return errMsg || '图片上传失败'
}

const parseErrorMessage = (data: string, fallback: string) => {
  try {
    const parsed = JSON.parse(data) as { detail?: unknown; message?: unknown }
    if (typeof parsed.detail === 'string') return parsed.detail
    if (typeof parsed.message === 'string') return parsed.message
  } catch {
    // keep fallback
  }
  return fallback
}

const uploadOneImage = (
  tripId: string,
  filePath: string,
  index: number,
  total: number,
  options: AiImportExtractOptions,
): Promise<AiExtractEventsResponse> => {
  const token = tokenStorage.get()
  return new Promise((resolve, reject) => {
    let settled = false
    let timedOut = false
    const timeout = setTimeout(() => {
      timedOut = true
      task.abort()
      if (!settled) {
        settled = true
        reject(new Error('识别耗时过长，请稍后重试或换一张更清晰的截图'))
      }
    }, options.timeoutMs ?? 120000)

    const task = uni.uploadFile({
      url: `${apiBaseUrl}/trips/${tripId}/ai/extract-events`,
      filePath,
      name: 'images',
      header: token ? { Authorization: `Bearer ${token}` } : {},
      formData: {},
      success: (res) => {
        if (settled) return
        settled = true
        clearTimeout(timeout)
        const status = res.statusCode ?? 0
        if (status >= 200 && status < 300) {
          try {
            resolve(JSON.parse(res.data) as AiExtractEventsResponse)
          } catch {
            reject(new Error('识别结果解析失败'))
          }
          return
        }
        reject(new Error(parseErrorMessage(res.data, `识别失败：HTTP ${status}`)))
      },
      fail: (err) => {
        if (settled) return
        settled = true
        clearTimeout(timeout)
        reject(new Error(timedOut ? '识别耗时过长，请稍后重试或换一张更清晰的截图' : formatUploadError(err.errMsg)))
      },
    }) as unknown as AiImportUploadTask & {
      onProgressUpdate?: (callback: (progress: { progress: number }) => void) => void
    }

    options.onUploadTask?.(task)
    options.onProgress?.({ phase: 'uploading', current: index + 1, total, uploadProgress: 0 })
    task.onProgressUpdate?.((progress) => {
      const uploadProgress = Math.max(0, Math.min(100, progress.progress || 0))
      options.onProgress?.({
        phase: uploadProgress >= 100 ? 'recognizing' : 'uploading',
        current: index + 1,
        total,
        uploadProgress,
      })
    })
  })
}

export const aiImportApi = {
  async extractTripEvents(
    tripId: string,
    filePaths: string[],
    options: AiImportExtractOptions = {},
  ): Promise<AiExtractEventsResponse> {
    const responses: AiExtractEventsResponse[] = []
    for (const [index, filePath] of filePaths.entries()) {
      responses.push(await uploadOneImage(tripId, filePath, index, filePaths.length, options))
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
