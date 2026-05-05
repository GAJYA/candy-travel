import { request } from './api'

export type ChecklistCategory =
  | 'document'
  | 'electronics'
  | 'clothing'
  | 'medicine'
  | 'food'
  | 'home'
  | 'pet'
  | 'task'
  | 'other'

export type ChecklistSource = 'template' | 'manual' | 'ai_generated'

export interface ChecklistTemplate {
  id: string
  label: string
  category: ChecklistCategory
  sortOrder: number
  isDefault: boolean
}

export interface ChecklistItem {
  id: string
  tripId: string
  label: string
  checked: boolean
  category: ChecklistCategory
  source: ChecklistSource
  templateId: string | null
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export interface ChecklistItemCreate {
  label: string
  category?: ChecklistCategory
  sortOrder?: number
  templateId?: string
  checked?: boolean
}

export interface ChecklistItemPatch {
  label?: string
  category?: ChecklistCategory
  sortOrder?: number
  checked?: boolean
}

export const CATEGORY_LABELS: Record<ChecklistCategory, string> = {
  document: '证件',
  electronics: '电子',
  clothing: '服饰',
  medicine: '药品',
  food: '食品',
  home: '家居',
  pet: '宠物',
  task: '事务',
  other: '其他',
}

export const checklistApi = {
  templates: () => request<ChecklistTemplate[]>('/checklist-templates'),
  list: (tripId: string) =>
    request<ChecklistItem[]>(`/trips/${tripId}/checklist-items`),
  create: (tripId: string, payload: ChecklistItemCreate) =>
    request<ChecklistItem>(`/trips/${tripId}/checklist-items`, {
      method: 'POST',
      data: payload,
    }),
  patch: (id: string, payload: ChecklistItemPatch) =>
    request<ChecklistItem>(`/checklist-items/${id}`, {
      method: 'PATCH',
      data: payload,
    }),
  delete: (id: string) =>
    request<void>(`/checklist-items/${id}`, { method: 'DELETE' }),
}
