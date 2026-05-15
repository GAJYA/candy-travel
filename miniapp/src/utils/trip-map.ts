import type { TripEvent } from '../services/trip-event'

export interface TripMapPoint {
  latitude: number
  longitude: number
}

export interface TripMapMarker extends TripMapPoint {
  id: number
  title: string
  iconPath: string
  width: number
  height: number
  alpha: number
  label: {
    content: string
    color: string
    fontSize: number
    borderRadius: number
    bgColor: string
    padding: number
    textAlign: 'center'
    anchorX: number
    anchorY: number
  }
  callout?: {
    content: string
    color: string
    fontSize: number
    borderRadius: number
    bgColor: string
    padding: number
    display: 'ALWAYS'
  }
}

export interface TripMapPolyline {
  points: TripMapPoint[]
  color: string
  width: number
  dottedLine: boolean
  arrowLine: boolean
}

export type TripMapFocusMode = 'all' | 'destination'

export interface TripMapData {
  mappableEvents: TripEvent[]
  missingLocationEvents: TripEvent[]
  markers: TripMapMarker[]
  polyline: TripMapPolyline[]
  includePoints: TripMapPoint[]
  center: TripMapPoint
  scale: number
  focusMode: TripMapFocusMode
  hasDestinationFocus: boolean
}

const DEFAULT_CENTER: TripMapPoint = {
  latitude: 30.27415,
  longitude: 120.15515,
}

const isFiniteCoordinate = (value: unknown): value is number => (
  typeof value === 'number' && Number.isFinite(value)
)

export const hasEventCoordinates = (event: Pick<TripEvent, 'latitude' | 'longitude'>) => (
  isFiniteCoordinate(event.latitude) && isFiniteCoordinate(event.longitude)
)

export const sortTripEventsForMap = (events: TripEvent[]) => (
  [...events].sort((a, b) => (
    new Date(a.startAt).getTime() - new Date(b.startAt).getTime()
    || a.sortOrder - b.sortOrder
    || a.title.localeCompare(b.title)
  ))
)

const eventLocationLabel = (event: TripEvent) => (
  event.locationName || event.title
)

const shouldPromptForMapLocation = (event: TripEvent) => (
  Boolean(event.locationName?.trim()) || event.eventType === 'activity'
)

const toMapPoint = (event: TripEvent): TripMapPoint => ({
  latitude: event.latitude as number,
  longitude: event.longitude as number,
})

const distanceKm = (a: TripMapPoint, b: TripMapPoint) => {
  const rad = Math.PI / 180
  const earthRadiusKm = 6371
  const dLat = (b.latitude - a.latitude) * rad
  const dLng = (b.longitude - a.longitude) * rad
  const lat1 = a.latitude * rad
  const lat2 = b.latitude * rad
  const h = Math.sin(dLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2
  return 2 * earthRadiusKm * Math.asin(Math.sqrt(h))
}

const LONG_DISTANCE_JUMP_KM = 50

const destinationRange = (events: TripEvent[]) => {
  const wholeRoute = { startIndex: 0, endIndex: events.length }
  if (events.length < 3) return wholeRoute

  let startIndex = 0
  for (let index = 1; index < events.length; index += 1) {
    const jumpKm = distanceKm(toMapPoint(events[index - 1]), toMapPoint(events[index]))
    if (jumpKm >= LONG_DISTANCE_JUMP_KM && events.length - index >= 2) {
      startIndex = index
      break
    }
  }

  let endIndex = events.length
  for (let index = events.length - 1; index > startIndex; index -= 1) {
    const jumpKm = distanceKm(toMapPoint(events[index - 1]), toMapPoint(events[index]))
    if (jumpKm >= LONG_DISTANCE_JUMP_KM && index - startIndex >= 2) {
      endIndex = index
      break
    }
  }

  return { startIndex, endIndex }
}

export const buildTripMapData = (
  events: TripEvent[],
  options: { focusMode?: TripMapFocusMode; selectedEventId?: string } = {},
): TripMapData => {
  const sorted = sortTripEventsForMap(events)
  const allMappableEvents = sorted.filter(hasEventCoordinates)
  const missingLocationEvents = sorted.filter((event) => (
    !hasEventCoordinates(event) && shouldPromptForMapLocation(event)
  ))
  const { startIndex, endIndex } = destinationRange(allMappableEvents)
  const hasDestinationFocus = startIndex > 0 || endIndex < allMappableEvents.length
  const focusMode = options.focusMode === 'all' || !hasDestinationFocus ? 'all' : 'destination'
  const mappableEvents = focusMode === 'destination'
    ? allMappableEvents.slice(startIndex, endIndex)
    : allMappableEvents
  const routePoints = mappableEvents.map(toMapPoint)
  const selectedEvent = mappableEvents.find((event) => event.id === options.selectedEventId)
  const selectedPoint = selectedEvent ? toMapPoint(selectedEvent) : null
  const includePoints = selectedPoint ? [] : routePoints
  const markers = mappableEvents.map((event, index) => {
    const isSelected = event.id === selectedEvent?.id
    return {
      id: index + 1,
      latitude: event.latitude as number,
      longitude: event.longitude as number,
      title: eventLocationLabel(event),
      iconPath: '/static/logo.png',
      width: 1,
      height: 1,
      alpha: 1,
      label: {
        content: String(index + 1),
        color: '#ffffff',
        fontSize: isSelected ? 13 : 11,
        borderRadius: 12,
        bgColor: isSelected ? '#7b4ab0' : '#e040a0',
        padding: isSelected ? 6 : 4,
        textAlign: 'center' as const,
        anchorX: isSelected ? -13 : -11,
        anchorY: isSelected ? -13 : -11,
      },
    }
  })

  return {
    mappableEvents,
    missingLocationEvents,
    markers,
    polyline: routePoints.length >= 2
      ? [{
          points: routePoints,
          color: '#e040a0',
          width: 4,
          dottedLine: false,
          arrowLine: true,
        }]
      : [],
    includePoints,
    center: selectedPoint || routePoints[0] || DEFAULT_CENTER,
    scale: selectedPoint ? 15 : 12,
    focusMode,
    hasDestinationFocus,
  }
}
