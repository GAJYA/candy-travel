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

export interface TripMapData {
  mappableEvents: TripEvent[]
  missingLocationEvents: TripEvent[]
  markers: TripMapMarker[]
  polyline: TripMapPolyline[]
  includePoints: TripMapPoint[]
  center: TripMapPoint
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

export const buildTripMapData = (events: TripEvent[]): TripMapData => {
  const sorted = sortTripEventsForMap(events)
  const mappableEvents = sorted.filter(hasEventCoordinates)
  const missingLocationEvents = sorted.filter((event) => !hasEventCoordinates(event))
  const includePoints = mappableEvents.map((event) => ({
    latitude: event.latitude as number,
    longitude: event.longitude as number,
  }))
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
  }
}
