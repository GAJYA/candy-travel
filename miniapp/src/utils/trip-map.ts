import type { TripEvent } from '../services/trip-event'

export interface TripMapPoint {
  latitude: number
  longitude: number
}

export interface TripMapMarker extends TripMapPoint {
  id: number
  title: string
  callout: {
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

const destinationStartIndex = (events: TripEvent[]) => {
  if (events.length < 3) return 0
  let maxJumpKm = 0
  let startIndex = 0
  for (let index = 1; index < events.length; index += 1) {
    const jumpKm = distanceKm(toMapPoint(events[index - 1]), toMapPoint(events[index]))
    if (jumpKm > maxJumpKm) {
      maxJumpKm = jumpKm
      startIndex = index
    }
  }
  return maxJumpKm >= 50 && events.length - startIndex >= 2 ? startIndex : 0
}

export const buildTripMapData = (
  events: TripEvent[],
  options: { focusMode?: TripMapFocusMode } = {},
): TripMapData => {
  const sorted = sortTripEventsForMap(events)
  const allMappableEvents = sorted.filter(hasEventCoordinates)
  const missingLocationEvents = sorted.filter((event) => (
    !hasEventCoordinates(event) && shouldPromptForMapLocation(event)
  ))
  const startIndex = destinationStartIndex(allMappableEvents)
  const hasDestinationFocus = startIndex > 0
  const focusMode = options.focusMode === 'all' || !hasDestinationFocus ? 'all' : 'destination'
  const mappableEvents = focusMode === 'destination'
    ? allMappableEvents.slice(startIndex)
    : allMappableEvents
  const includePoints = mappableEvents.map(toMapPoint)
  const markers = mappableEvents.map((event, index) => ({
    id: index + 1,
    latitude: event.latitude as number,
    longitude: event.longitude as number,
    title: eventLocationLabel(event),
    callout: {
      content: `${index + 1}. ${eventLocationLabel(event)}`,
      color: '#281330',
      fontSize: 12,
      borderRadius: 8,
      bgColor: '#ffffff',
      padding: 8,
      display: 'ALWAYS' as const,
    },
  }))

  return {
    mappableEvents,
    missingLocationEvents,
    markers,
    polyline: includePoints.length >= 2
      ? [{
          points: includePoints,
          color: '#e040a0',
          width: 5,
          dottedLine: false,
          arrowLine: true,
        }]
      : [],
    includePoints,
    center: includePoints[0] || DEFAULT_CENTER,
    focusMode,
    hasDestinationFocus,
  }
}
