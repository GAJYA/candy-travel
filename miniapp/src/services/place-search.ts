import { request } from './api'

export interface PlaceSuggestion {
  id: string
  title: string
  address: string
  category: string | null
  city: string | null
  district: string | null
  latitude: number
  longitude: number
}

export interface PlaceSearchParams {
  keyword: string
  region?: string
  latitude?: number | null
  longitude?: number | null
  pageSize?: number
}

const toQuery = (params: PlaceSearchParams) => {
  const query: string[] = []
  const add = (key: string, value: string | number) => {
    query.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
  }

  add('keyword', params.keyword)
  if (params.region) add('region', params.region)
  if (typeof params.latitude === 'number' && typeof params.longitude === 'number') {
    add('latitude', params.latitude)
    add('longitude', params.longitude)
  }
  if (params.pageSize) add('pageSize', params.pageSize)
  return query.join('&')
}

export const placeSearchApi = {
  search: (params: PlaceSearchParams) =>
    request<PlaceSuggestion[]>(`/places/search?${toQuery(params)}`),
}
