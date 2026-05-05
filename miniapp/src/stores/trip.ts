import { defineStore } from 'pinia'
import { ref } from 'vue'

import { tripApi, type Trip, type TripDetail } from '../services/trip'

export const useTripStore = defineStore('trip', () => {
  const list = ref<Trip[]>([])
  const listLoading = ref(false)
  const detail = ref<TripDetail | null>(null)
  const detailLoading = ref(false)
  const error = ref<string>('')

  const loadList = async () => {
    listLoading.value = true
    error.value = ''
    try {
      list.value = await tripApi.list()
    } catch (e) {
      error.value = formatError(e)
    } finally {
      listLoading.value = false
    }
  }

  const loadDetail = async (id: string) => {
    detailLoading.value = true
    error.value = ''
    try {
      detail.value = await tripApi.get(id)
    } catch (e) {
      error.value = formatError(e)
      detail.value = null
    } finally {
      detailLoading.value = false
    }
  }

  const clearDetail = () => {
    detail.value = null
  }

  return {
    list,
    listLoading,
    detail,
    detailLoading,
    error,
    loadList,
    loadDetail,
    clearDetail,
  }
})

const formatError = (e: unknown): string => {
  if (e instanceof Error) return e.message
  return String(e)
}
